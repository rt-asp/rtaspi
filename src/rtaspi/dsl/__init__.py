"""
Domain Specific Language (DSL) for pipeline configuration.

This module provides a simple DSL for defining processing pipelines. The DSL
allows users to define pipelines with sources, filters, and outputs in a
readable text format.

Example usage:

```python
from rtaspi.dsl import execute_pipeline_text

# Define pipeline using DSL
pipeline_text = '''
pipeline face_detection parallel {
    # Source stage from webcam
    source camera from webcam with {
        resolution = "1280x720",
        framerate = 30
    }

    # Face detection filter
    filter detect: FACE_DETECTION from camera with {
        method = "dnn",
        confidence = 0.5
    }

    # RTSP output
    output stream: RTSP from detect with {
        url = "rtsp://localhost:8554/face_detect",
        format = "h264"
    }
}
'''

# Execute pipeline
executor = execute_pipeline_text(pipeline_text)

# Stop pipeline when done
executor.stop()
```

The DSL syntax is designed to be simple and readable:

1. Pipeline Definition:
   ```
   pipeline name [parallel|sequential] {
       stages...
   }
   ```

2. Source Stage:
   ```
   source name from device [with {
       param = value,
       ...
   }]
   ```

3. Filter Stage:
   ```
   filter name: type from input [with {
       param = value,
       ...
   }]
   ```

4. Output Stage:
   ```
   output name: type from input [with {
       param = value,
       ...
   }]
   ```

5. Multiple Inputs:
   ```
   filter name: type from {input1, input2} [with {
       param = value,
       ...
   }]
   ```

6. Comments:
   ```
   # Single line comment
   ```

Parameter values can be:
- Numbers (e.g., 42, 3.14)
- Strings (e.g., "hello")
- Identifiers (e.g., dnn, h264)
"""

from .lexer import Lexer, Token, TokenType
from .parser import Parser, Pipeline, Source, Filter, Output
from .executor import Executor, execute_pipeline_file, execute_pipeline_text

__all__ = [
    # Main functions
    "execute_pipeline_file",
    "execute_pipeline_text",
    # Classes
    "Lexer",
    "Parser",
    "Executor",
    "Pipeline",
    "Source",
    "Filter",
    "Output",
    "Token",
    "TokenType",
]

# Version history:
# 1.0.0 - Initial release with basic DSL functionality
#       - Lexer, parser, and executor implementation
#       - Support for sources, filters, and outputs
#       - Parameter validation and error handling
