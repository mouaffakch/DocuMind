from typing import List, Dict, Set, Tuple, Optional
from uuid import UUID
from collections import deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dependency import SymbolDependency
from app.models.code_symbol import CodeSymbol
from app.models.code_file import CodeFile
from app.schemas.impact import (
    GraphNode,
    GraphEdge,
    RiskAssessment,
    ImpactAnalysisResponse,
    SymbolAutocompleteResponse,
)
from app.core.exceptions import EntityNotFoundError


class ImpactService:
    """Service performing deterministic static call-graph analysis and regression risk assessment."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_impact(
        self,
        project_id: UUID,
        target_symbol: str,
        max_depth: int = 3,
    ) -> ImpactAnalysisResponse:
        """
        Computes the reverse call graph starting from the target symbol,
        identifying direct and transitive callers, affected files, and recommended test suites.
        """
        clean_target = target_symbol.strip()

        # 1. Fetch target symbol details if indexed
        sym_stmt = (
            select(CodeSymbol, CodeFile.file_path)
            .join(CodeFile, CodeSymbol.file_id == CodeFile.id)
            .where(CodeFile.project_id == project_id, CodeSymbol.name.ilike(f"%{clean_target}%"))
        )
        sym_res = await self.session.execute(sym_stmt)
        target_record = sym_res.first()

        target_file = target_record[1] if target_record else "unknown"
        target_line = target_record[0].start_line if target_record else 1

        # 2. Fetch all dependency edges for this project
        dep_stmt = select(SymbolDependency).where(SymbolDependency.project_id == project_id)
        dep_res = await self.session.execute(dep_stmt)
        all_deps = list(dep_res.scalars().all())

        # Build reverse adjacency map: callee -> list of (caller_name, caller_file, caller_line, dep_type)
        reverse_graph: Dict[str, List[SymbolDependency]] = {}
        for dep in all_deps:
            callee_key = dep.callee_name.lower()
            reverse_graph.setdefault(callee_key, []).append(dep)

        # 3. BFS reverse traversal
        visited_nodes: Set[str] = {clean_target.lower()}
        queue = deque([(clean_target.lower(), 1)])  # (symbol_name, current_depth)

        nodes: List[GraphNode] = [
            GraphNode(
                id=f"target-{clean_target}",
                label=clean_target,
                symbol_name=clean_target,
                file_path=target_file,
                line=target_line,
                node_type="target",
            )
        ]
        edges: List[GraphEdge] = []
        direct_callers: Set[str] = set()
        transitive_callers: Set[str] = set()
        impacted_files: Set[str] = {target_file} if target_file != "unknown" else set()
        affected_tests: Set[str] = set()

        while queue:
            current_sym, depth = queue.popleft()
            if depth > max_depth:
                continue

            incoming_calls = reverse_graph.get(current_sym, [])
            for call in incoming_calls:
                caller_key = call.caller_name.lower()
                is_test = any(t in call.caller_file_path.lower() for t in ("test", "spec", "__tests__"))

                node_id = f"node-{call.caller_file_path}-{call.caller_name}"

                if depth == 1:
                    direct_callers.add(call.caller_name)
                else:
                    transitive_callers.add(call.caller_name)

                impacted_files.add(call.caller_file_path)
                if is_test:
                    affected_tests.add(call.caller_file_path)

                if caller_key not in visited_nodes:
                    visited_nodes.add(caller_key)
                    nodes.append(
                        GraphNode(
                            id=node_id,
                            label=call.caller_name,
                            symbol_name=call.caller_name,
                            file_path=call.caller_file_path,
                            line=call.caller_line,
                            node_type="test" if is_test else "caller",
                        )
                    )
                    queue.append((caller_key, depth + 1))

                # Edge from Caller -> Callee
                edge_id = f"edge-{call.caller_name}->{current_sym}-{call.caller_line}"
                target_node_id = f"target-{clean_target}" if current_sym == clean_target.lower() else f"node-{call.caller_file_path}-{current_sym}"
                edges.append(
                    GraphEdge(
                        id=edge_id,
                        source=node_id,
                        target=target_node_id,
                        edge_type=call.dependency_type.value,
                    )
                )

        # 4. Compute Risk Assessment
        total_callers = len(direct_callers) + len(transitive_callers)
        num_files = len(impacted_files)
        num_tests = len(affected_tests)

        if total_callers >= 8 or num_files >= 5:
            risk_level = "CRITICAL"
            risk_score = 0.95
            explanation = (
                f"Impact CRITIQUE : La fonction '{clean_target}' possède {len(direct_callers)} appelants directs "
                f"et {len(transitive_callers)} appelants transitifs répartis sur {num_files} fichiers. "
                f"Une modification sans précaution présente un risque élevé de régression majeure."
            )
        elif total_callers >= 4 or num_files >= 3:
            risk_level = "HIGH"
            risk_score = 0.75
            explanation = (
                f"Impact ÉLEVÉ : {total_callers} composants dépendent directement ou indirectement de cette fonction. "
                f"{num_tests} suite(s) de tests automatisés doivent impérativement être revalidées."
            )
        elif total_callers >= 1:
            risk_level = "MEDIUM"
            risk_score = 0.45
            explanation = (
                f"Impact MODÉRÉ : {total_callers} composant(s) dépendant(s) identifié(s). "
                f"La modification est localisée."
            )
        else:
            risk_level = "LOW"
            risk_score = 0.1
            explanation = (
                f"Impact FAIBLE : Aucun appelant direct n'a été détecté dans les autres fichiers du projet. "
                f"La fonction semble isolée ou appelée dynamiquement."
            )

        return ImpactAnalysisResponse(
            target_symbol=clean_target,
            target_file=target_file,
            target_line=target_line,
            nodes=nodes,
            edges=edges,
            impacted_files=sorted(list(impacted_files)),
            affected_tests=sorted(list(affected_tests)),
            risk_assessment=RiskAssessment(
                level=risk_level,
                score=risk_score,
                direct_callers_count=len(direct_callers),
                transitive_callers_count=len(transitive_callers),
                affected_files_count=num_files,
                affected_tests_count=num_tests,
                explanation=explanation,
            ),
        )

    async def search_symbols(
        self,
        project_id: UUID,
        query: str,
        limit: int = 15,
    ) -> List[SymbolAutocompleteResponse]:
        """Search indexed symbols for UI autocomplete."""
        stmt = (
            select(CodeSymbol, CodeFile.file_path)
            .join(CodeFile, CodeSymbol.file_id == CodeFile.id)
            .where(CodeFile.project_id == project_id, CodeSymbol.name.ilike(f"%{query.strip()}%"))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        records = res.all()

        return [
            SymbolAutocompleteResponse(
                id=sym.id,
                name=sym.name,
                symbol_type=sym.symbol_type.value,
                file_path=fpath,
                start_line=sym.start_line,
                signature=sym.signature,
            )
            for sym, fpath in records
        ]
