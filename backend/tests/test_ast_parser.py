import pytest
from app.ingestion.ast_parser import ASTParser
from app.models.code_symbol import SymbolType


def test_parse_python_code():
    code = """
\"\"\"Authentication module.\"\"\"

class AuthenticationManager:
    \"\"\"Manages user logins and sessions.\"\"\"
    
    def __init__(self, secret: str):
        self.secret = secret

    def authenticate_user(self, username: str, password: str) -> bool:
        \"\"\"Verify user credentials.\"\"\"
        return True

def hash_password(plain: str) -> str:
    \"\"\"Compute secure hash.\"\"\"
    return "hashed_" + plain
"""
    symbols = ASTParser.parse_code(code, "python")
    names = [s.name for s in symbols]

    assert "AuthenticationManager" in names
    assert "AuthenticationManager.__init__" in names
    assert "AuthenticationManager.authenticate_user" in names
    assert "hash_password" in names

    # Check symbol types
    class_sym = next(s for s in symbols if s.name == "AuthenticationManager")
    assert class_sym.symbol_type == SymbolType.CLASS
    assert class_sym.docstring == "Manages user logins and sessions."

    func_sym = next(s for s in symbols if s.name == "hash_password")
    assert func_sym.symbol_type == SymbolType.FUNCTION
    assert func_sym.start_line == 14
    assert func_sym.end_line == 16
    assert "hash_password(plain: str)" in func_sym.signature


def test_parse_typescript_code():
    code = """
interface UserDTO {
    id: string;
    email: string;
}

export class UserService {
    private db: any;

    async findUserById(id: string): Promise<UserDTO> {
        return { id, email: "test@example.com" };
    }
}

export function validateEmail(email: string): boolean {
    return email.includes("@");
}
"""
    symbols = ASTParser.parse_code(code, "typescript")
    names = [s.name for s in symbols]

    assert "UserDTO" in names
    assert "UserService" in names
    assert "UserService.findUserById" in names
    assert "validateEmail" in names

    dto_sym = next(s for s in symbols if s.name == "UserDTO")
    assert dto_sym.symbol_type == SymbolType.INTERFACE

    class_sym = next(s for s in symbols if s.name == "UserService")
    assert class_sym.symbol_type == SymbolType.CLASS


def test_parse_go_code():
    code = """
package main

import "fmt"

func CalculateTotal(items []int) int {
    sum := 0
    for _, item := range items {
        sum += item
    }
    return sum
}
"""
    symbols = ASTParser.parse_code(code, "go")
    names = [s.name for s in symbols]
    assert "CalculateTotal" in names
    sym = symbols[0]
    assert sym.symbol_type == SymbolType.FUNCTION
    assert sym.start_line == 6
