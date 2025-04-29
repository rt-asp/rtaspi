"""
DSL lexer implementation.

This module provides a simple lexer for the pipeline DSL, which tokenizes
input text into a stream of tokens for the parser.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token types for the DSL lexer."""

    # Keywords
    PIPELINE = auto()
    SOURCE = auto()
    FILTER = auto()
    OUTPUT = auto()
    FROM = auto()
    TO = auto()
    WITH = auto()
    PARALLEL = auto()
    SEQUENTIAL = auto()

    # Identifiers and literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Punctuation
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    COMMA = auto()  # ,
    COLON = auto()  # :
    ARROW = auto()  # ->
    EQUALS = auto()  # =

    # Special
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    """Token class representing a lexical unit."""

    type: TokenType
    value: str
    line: int
    column: int


class Lexer:
    """DSL lexer implementation."""

    def __init__(self, text: str):
        """Initialize the lexer.

        Args:
            text: Input text to tokenize
        """
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = text[0] if text else None

        # Keywords mapping
        self.keywords = {
            "pipeline": TokenType.PIPELINE,
            "source": TokenType.SOURCE,
            "filter": TokenType.FILTER,
            "output": TokenType.OUTPUT,
            "from": TokenType.FROM,
            "to": TokenType.TO,
            "with": TokenType.WITH,
            "parallel": TokenType.PARALLEL,
            "sequential": TokenType.SEQUENTIAL,
        }

    def advance(self) -> None:
        """Advance the current character."""
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]
            if self.current_char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self) -> None:
        """Skip comment lines."""
        while self.current_char and self.current_char != "\n":
            self.advance()
        if self.current_char == "\n":
            self.advance()

    def read_identifier(self) -> Token:
        """Read an identifier or keyword.

        Returns:
            Token representing the identifier or keyword
        """
        start_column = self.column
        result = ""
        while self.current_char and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            result += self.current_char
            self.advance()

        # Check if it's a keyword
        token_type = self.keywords.get(result.lower(), TokenType.IDENTIFIER)
        return Token(token_type, result, self.line, start_column)

    def read_number(self) -> Token:
        """Read a number.

        Returns:
            Token representing the number
        """
        start_column = self.column
        result = ""
        while self.current_char and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, result, self.line, start_column)

    def read_string(self) -> Token:
        """Read a string literal.

        Returns:
            Token representing the string
        """
        start_column = self.column
        self.advance()  # Skip opening quote
        result = ""
        while self.current_char and self.current_char != '"':
            if self.current_char == "\\":
                self.advance()
                if self.current_char == "n":
                    result += "\n"
                elif self.current_char == "t":
                    result += "\t"
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()

        if self.current_char == '"':
            self.advance()  # Skip closing quote
            return Token(TokenType.STRING, result, self.line, start_column)
        else:
            return Token(
                TokenType.ERROR, "Unterminated string", self.line, start_column
            )

    def get_next_token(self) -> Token:
        """Get the next token from the input.

        Returns:
            Next token from the input stream
        """
        while self.current_char:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Skip comments
            if self.current_char == "#":
                self.skip_comment()
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                return self.read_identifier()

            # Numbers
            if self.current_char.isdigit():
                return self.read_number()

            # Strings
            if self.current_char == '"':
                return self.read_string()

            # Arrow operator
            if (
                self.current_char == "-"
                and self.pos + 1 < len(self.text)
                and self.text[self.pos + 1] == ">"
            ):
                token = Token(TokenType.ARROW, "->", self.line, self.column)
                self.advance()
                self.advance()
                return token

            # Single-character tokens
            char_tokens = {
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                ",": TokenType.COMMA,
                ":": TokenType.COLON,
                "=": TokenType.EQUALS,
            }

            if self.current_char in char_tokens:
                token = Token(
                    char_tokens[self.current_char],
                    self.current_char,
                    self.line,
                    self.column,
                )
                self.advance()
                return token

            # Invalid character
            token = Token(
                TokenType.ERROR,
                f"Invalid character: {self.current_char}",
                self.line,
                self.column,
            )
            self.advance()
            return token

        # End of file
        return Token(TokenType.EOF, "", self.line, self.column)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input.

        Returns:
            List of tokens from the input
        """
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type in (TokenType.EOF, TokenType.ERROR):
                break
        return tokens
