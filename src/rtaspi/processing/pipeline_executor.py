"""
Pipeline execution implementation.

This module provides pipeline execution capabilities, including:
- Stage execution and chaining
- Parallel processing
- Resource management
- Error handling
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from rtaspi.schemas import PipelineConfig, PipelineStage
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.processing.video.detection import ObjectDetector, FaceDetector
from rtaspi.processing.audio.filters import AudioFilter
from rtaspi.processing.audio.speech import SpeechRecognizer


class PipelineExecutor:
    """Pipeline execution handler."""

    def __init__(self, config: PipelineConfig, max_workers: Optional[int] = None):
        """Initialize the pipeline executor.

        Args:
            config: Pipeline configuration
            max_workers: Maximum number of worker threads
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.stages: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.error = None

        # Initialize stages
        self._init_stages()

    def _init_stages(self) -> None:
        """Initialize pipeline stages."""
        for stage in self.config.stages:
            # Create stage instance based on type
            if stage.type == "VIDEO_FILTER":
                self.stages[stage.name] = VideoFilter(
                    filter_type=stage.filter_type, params=stage.params
                )
            elif stage.type == "OBJECT_DETECTION":
                self.stages[stage.name] = ObjectDetector(**stage.params)
            elif stage.type == "FACE_DETECTION":
                self.stages[stage.name] = FaceDetector(**stage.params)
            elif stage.type == "AUDIO_FILTER":
                self.stages[stage.name] = AudioFilter(
                    filter_type=stage.filter_type, params=stage.params
                )
            elif stage.type == "SPEECH_RECOGNITION":
                self.stages[stage.name] = SpeechRecognizer(**stage.params)
            else:
                raise ValueError(f"Unsupported stage type: {stage.type}")

    async def start(self) -> None:
        """Start pipeline execution."""
        if self.running:
            raise RuntimeError("Pipeline is already running")

        self.running = True
        self.error = None

        try:
            # Start stages in parallel if enabled
            if self.config.execution_settings.parallel_execution:
                await self._run_parallel()
            else:
                await self._run_sequential()

        except Exception as e:
            self.error = str(e)
            self.logger.error(f"Pipeline error: {e}")
            raise

        finally:
            self.running = False

    async def stop(self) -> None:
        """Stop pipeline execution."""
        self.running = False
        self.executor.shutdown(wait=True)

    async def _run_parallel(self) -> None:
        """Run pipeline stages in parallel."""
        # Group stages by level (stages that can run in parallel)
        levels = self._group_stages_by_level()

        # Process levels sequentially, but stages within each level in parallel
        for level in levels:
            tasks = []
            for stage in level:
                task = asyncio.create_task(self._run_stage(stage))
                tasks.append(task)

            # Wait for all stages in this level to complete
            await asyncio.gather(*tasks)

    async def _run_sequential(self) -> None:
        """Run pipeline stages sequentially."""
        # Sort stages by dependencies
        ordered_stages = self._sort_stages()

        # Process stages sequentially
        for stage in ordered_stages:
            await self._run_stage(stage)

    async def _run_stage(self, stage: PipelineStage) -> None:
        """Run a single pipeline stage.

        Args:
            stage: Stage configuration
        """
        if not self.running:
            return

        try:
            # Get stage instance
            instance = self.stages[stage.name]

            # Get input data from previous stages
            inputs = []
            for input_name in stage.inputs:
                input_stage = self.stages[input_name]
                inputs.append(await self._get_stage_output(input_stage))

            # Process stage
            if len(inputs) == 0:
                # Source stage
                output = await self._process_stage(instance, None)
            elif len(inputs) == 1:
                # Single input stage
                output = await self._process_stage(instance, inputs[0])
            else:
                # Multiple input stage
                output = await self._process_stage(instance, inputs)

            # Store output
            instance.output = output

        except Exception as e:
            # Handle error based on configuration
            if self.config.error_handling.stop_on_error:
                raise
            else:
                self.logger.error(f"Stage {stage.name} error: {e}")
                instance.output = None

    async def _process_stage(self, instance: Any, input_data: Any) -> Any:
        """Process a stage with input data.

        Args:
            instance: Stage instance
            input_data: Input data

        Returns:
            Stage output
        """
        # Check resource limits
        if self.config.resource_limits:
            self._check_resource_limits()

        # Process in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._process_stage_sync, instance, input_data
        )

    def _process_stage_sync(self, instance: Any, input_data: Any) -> Any:
        """Process a stage synchronously.

        Args:
            instance: Stage instance
            input_data: Input data

        Returns:
            Stage output
        """
        if isinstance(instance, (VideoFilter, AudioFilter)):
            return instance.apply(input_data)
        elif isinstance(instance, (ObjectDetector, FaceDetector)):
            return instance.detect(input_data)
        elif isinstance(instance, SpeechRecognizer):
            return instance.recognize(input_data)
        else:
            raise ValueError(f"Unsupported stage type: {type(instance)}")

    async def _get_stage_output(self, stage: Any) -> Any:
        """Get stage output, waiting if not ready.

        Args:
            stage: Stage instance

        Returns:
            Stage output
        """
        # Wait for output to be available
        while self.running and not hasattr(stage, "output"):
            await asyncio.sleep(0.1)

        return stage.output if self.running else None

    def _group_stages_by_level(self) -> List[List[PipelineStage]]:
        """Group stages by level for parallel execution.

        Returns:
            List of stage lists, where each inner list contains
            stages that can be executed in parallel
        """
        levels = []
        remaining = set(s.name for s in self.config.stages)
        processed = set()

        while remaining:
            # Find stages whose inputs are all processed
            current_level = []
            for stage in self.config.stages:
                if stage.name in remaining and all(
                    i in processed for i in stage.inputs
                ):
                    current_level.append(stage)

            # Add level
            levels.append(current_level)
            processed.update(s.name for s in current_level)
            remaining.difference_update(processed)

        return levels

    def _sort_stages(self) -> List[PipelineStage]:
        """Sort stages by dependencies for sequential execution.

        Returns:
            Ordered list of stages
        """
        ordered = []
        remaining = set(s.name for s in self.config.stages)
        processed = set()

        while remaining:
            # Find stage whose inputs are all processed
            for stage in self.config.stages:
                if stage.name in remaining and all(
                    i in processed for i in stage.inputs
                ):
                    ordered.append(stage)
                    processed.add(stage.name)
                    remaining.remove(stage.name)
                    break
            else:
                raise ValueError("Circular dependency detected")

        return ordered

    def _check_resource_limits(self) -> None:
        """Check resource usage against limits."""
        import psutil

        process = psutil.Process()
        limits = self.config.resource_limits

        # Check CPU usage
        if limits.max_cpu_percent:
            cpu_percent = process.cpu_percent()
            if cpu_percent > limits.max_cpu_percent:
                raise RuntimeError(
                    f"CPU usage ({cpu_percent}%) exceeds limit "
                    f"({limits.max_cpu_percent}%)"
                )

        # Check memory usage
        if limits.max_memory_mb:
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > limits.max_memory_mb:
                raise RuntimeError(
                    f"Memory usage ({memory_mb:.1f}MB) exceeds limit "
                    f"({limits.max_memory_mb}MB)"
                )
