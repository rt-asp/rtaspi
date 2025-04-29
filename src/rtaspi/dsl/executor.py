"""
DSL executor implementation.

This module provides an executor for the pipeline DSL, which takes the AST
from the parser and executes it using the pipeline executor.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from rtaspi.schemas import PipelineConfig, PipelineStage
from rtaspi.processing.pipeline_executor import PipelineExecutor
from .parser import Pipeline, Source, Filter, Output, Node


class Executor:
    """DSL executor implementation."""

    def __init__(self):
        """Initialize the executor."""
        self.stages: Dict[str, PipelineStage] = {}
        self.executor: Optional[PipelineExecutor] = None

    def execute(self, ast: Pipeline) -> None:
        """Execute a pipeline AST.

        Args:
            ast: Pipeline AST from the parser
        """
        # Convert AST to pipeline configuration
        config = self._create_pipeline_config(ast)

        # Create and start pipeline executor
        self.executor = PipelineExecutor(config)
        self.executor.start()

    def stop(self) -> None:
        """Stop pipeline execution."""
        if self.executor:
            self.executor.stop()
            self.executor = None

    def _create_pipeline_config(self, ast: Pipeline) -> PipelineConfig:
        """Create pipeline configuration from AST.

        Args:
            ast: Pipeline AST

        Returns:
            Pipeline configuration
        """
        # Clear existing stages
        self.stages.clear()

        # Convert AST nodes to pipeline stages
        stages = []
        for node in ast.stages:
            stage = self._convert_node(node)
            stages.append(stage)
            self.stages[stage.name] = stage

        # Create pipeline configuration
        return PipelineConfig(
            name=ast.name,
            enabled=True,
            stages=stages,
            execution_settings={"parallel_execution": ast.parallel},
            resource_limits={"max_cpu_percent": 80, "max_memory_mb": 1024},
            error_handling={
                "stop_on_error": True,
                "retry_count": 3,
                "retry_delay": 1.0,
            },
        )

    def _convert_node(self, node: Node) -> PipelineStage:
        """Convert an AST node to a pipeline stage.

        Args:
            node: AST node

        Returns:
            Pipeline stage configuration
        """
        if isinstance(node, Source):
            return self._convert_source(node)
        elif isinstance(node, Filter):
            return self._convert_filter(node)
        elif isinstance(node, Output):
            return self._convert_output(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

    def _convert_source(self, node: Source) -> PipelineStage:
        """Convert a source node to a pipeline stage.

        Args:
            node: Source node

        Returns:
            Pipeline stage configuration
        """
        return PipelineStage(
            name=node.name,
            type="SOURCE",
            enabled=True,
            device=node.device,
            inputs=[],
            outputs=[],
            params=node.params,
        )

    def _convert_filter(self, node: Filter) -> PipelineStage:
        """Convert a filter node to a pipeline stage.

        Args:
            node: Filter node

        Returns:
            Pipeline stage configuration
        """
        # Validate input stages exist
        for input_name in node.inputs:
            if input_name not in self.stages:
                raise ValueError(f"Unknown input stage: {input_name}")

        return PipelineStage(
            name=node.name,
            type=node.type,
            enabled=True,
            inputs=node.inputs,
            outputs=[],
            params=node.params,
        )

    def _convert_output(self, node: Output) -> PipelineStage:
        """Convert an output node to a pipeline stage.

        Args:
            node: Output node

        Returns:
            Pipeline stage configuration
        """
        # Validate input stages exist
        for input_name in node.inputs:
            if input_name not in self.stages:
                raise ValueError(f"Unknown input stage: {input_name}")

        return PipelineStage(
            name=node.name,
            type=node.type,
            enabled=True,
            inputs=node.inputs,
            outputs=[],
            params=node.params,
        )


def execute_pipeline_file(path: str) -> Executor:
    """Execute a pipeline from a DSL file.

    Args:
        path: Path to DSL file

    Returns:
        Pipeline executor
    """
    from .lexer import Lexer
    from .parser import Parser

    # Read file
    with open(path) as f:
        text = f.read()

    # Parse pipeline
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Execute pipeline
    executor = Executor()
    executor.execute(ast)
    return executor


def execute_pipeline_text(text: str) -> Executor:
    """Execute a pipeline from DSL text.

    Args:
        text: DSL text

    Returns:
        Pipeline executor
    """
    from .lexer import Lexer
    from .parser import Parser

    # Parse pipeline
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    # Execute pipeline
    executor = Executor()
    executor.execute(ast)
    return executor
