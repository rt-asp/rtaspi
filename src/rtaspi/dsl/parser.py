"""
DSL parser implementation.

This module provides a parser for the pipeline DSL, which takes tokens from
the lexer and builds an Abstract Syntax Tree (AST) for pipeline configuration.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .lexer import Token, TokenType


@dataclass
class Node:
    """Base class for AST nodes."""

    pass


@dataclass
class Pipeline(Node):
    """Pipeline definition node."""

    name: str
    parallel: bool
    stages: List[Node]


@dataclass
class Source(Node):
    """Source stage node."""

    name: str
    device: str
    params: Dict[str, Any]


@dataclass
class Filter(Node):
    """Filter stage node."""

    name: str
    type: str
    inputs: List[str]
    params: Dict[str, Any]


@dataclass
class Output(Node):
    """Output stage node."""

    name: str
    type: str
    inputs: List[str]
    params: Dict[str, Any]


class Parser:
    """DSL parser implementation."""

    def __init__(self, tokens: List[Token]):
        """Initialize the parser.

        Args:
            tokens: List of tokens from the lexer
        """
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None

    def error(self, message: str) -> None:
        """Raise a syntax error.

        Args:
            message: Error message
        """
        if self.current_token:
            raise SyntaxError(
                f"{message} at line {self.current_token.line}, "
                f"column {self.current_token.column}"
            )
        else:
            raise SyntaxError(message)

    def advance(self) -> None:
        """Advance to the next token."""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def eat(self, token_type: TokenType) -> Token:
        """Consume a token of the expected type.

        Args:
            token_type: Expected token type

        Returns:
            Consumed token
        """
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        else:
            self.error(f"Expected {token_type}, got {self.current_token}")

    def parse(self) -> Pipeline:
        """Parse the input tokens into an AST.

        Returns:
            Root node of the AST
        """
        return self.parse_pipeline()

    def parse_pipeline(self) -> Pipeline:
        """Parse a pipeline definition.

        Returns:
            Pipeline node
        """
        # pipeline name { ... }
        self.eat(TokenType.PIPELINE)
        name = self.eat(TokenType.IDENTIFIER).value

        # Check for execution mode
        parallel = True
        if self.current_token and self.current_token.type in (
            TokenType.PARALLEL,
            TokenType.SEQUENTIAL,
        ):
            parallel = self.current_token.type == TokenType.PARALLEL
            self.advance()

        self.eat(TokenType.LBRACE)
        stages = []

        # Parse stages until closing brace
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.SOURCE:
                stages.append(self.parse_source())
            elif self.current_token.type == TokenType.FILTER:
                stages.append(self.parse_filter())
            elif self.current_token.type == TokenType.OUTPUT:
                stages.append(self.parse_output())
            else:
                self.error("Expected source, filter, or output")

        self.eat(TokenType.RBRACE)
        return Pipeline(name, parallel, stages)

    def parse_source(self) -> Source:
        """Parse a source stage.

        Returns:
            Source node
        """
        # source name from device with { ... }
        self.eat(TokenType.SOURCE)
        name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.FROM)
        device = self.eat(TokenType.IDENTIFIER).value

        # Parse optional parameters
        params = {}
        if self.current_token and self.current_token.type == TokenType.WITH:
            self.advance()
            params = self.parse_params()

        return Source(name, device, params)

    def parse_filter(self) -> Filter:
        """Parse a filter stage.

        Returns:
            Filter node
        """
        # filter name: type from [inputs] with { ... }
        self.eat(TokenType.FILTER)
        name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.COLON)
        filter_type = self.eat(TokenType.IDENTIFIER).value

        # Parse inputs
        self.eat(TokenType.FROM)
        inputs = self.parse_input_list()

        # Parse optional parameters
        params = {}
        if self.current_token and self.current_token.type == TokenType.WITH:
            self.advance()
            params = self.parse_params()

        return Filter(name, filter_type, inputs, params)

    def parse_output(self) -> Output:
        """Parse an output stage.

        Returns:
            Output node
        """
        # output name: type from [inputs] with { ... }
        self.eat(TokenType.OUTPUT)
        name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.COLON)
        output_type = self.eat(TokenType.IDENTIFIER).value

        # Parse inputs
        self.eat(TokenType.FROM)
        inputs = self.parse_input_list()

        # Parse optional parameters
        params = {}
        if self.current_token and self.current_token.type == TokenType.WITH:
            self.advance()
            params = self.parse_params()

        return Output(name, output_type, inputs, params)

    def parse_input_list(self) -> List[str]:
        """Parse a list of input stage names.

        Returns:
            List of input stage names
        """
        inputs = []

        # Single input without brackets
        if self.current_token.type == TokenType.IDENTIFIER:
            inputs.append(self.eat(TokenType.IDENTIFIER).value)
            return inputs

        # Multiple inputs with brackets
        self.eat(TokenType.LBRACE)
        while True:
            inputs.append(self.eat(TokenType.IDENTIFIER).value)
            if self.current_token.type != TokenType.COMMA:
                break
            self.advance()  # Skip comma
        self.eat(TokenType.RBRACE)

        return inputs

    def parse_params(self) -> Dict[str, Any]:
        """Parse parameter key-value pairs.

        Returns:
            Dictionary of parameters
        """
        params = {}

        self.eat(TokenType.LBRACE)
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            # Parse key
            key = self.eat(TokenType.IDENTIFIER).value
            self.eat(TokenType.EQUALS)

            # Parse value
            if self.current_token.type == TokenType.NUMBER:
                value = float(self.current_token.value)
                self.advance()
            elif self.current_token.type == TokenType.STRING:
                value = self.current_token.value
                self.advance()
            elif self.current_token.type == TokenType.IDENTIFIER:
                value = self.current_token.value
                self.advance()
            else:
                self.error("Expected number, string, or identifier")

            params[key] = value

            # Skip comma if present
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self.advance()

        self.eat(TokenType.RBRACE)
        return params
