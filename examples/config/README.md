# rtaspi Configuration System

rtaspi uses a hierarchical configuration system that allows settings to be defined at different levels, with each level overriding the settings from the previous level. This provides flexibility in managing configurations across different scopes.

## Configuration Hierarchy

The configuration is loaded in the following order (later levels override earlier ones):

1. **Default Configuration** (`src/rtaspi/core/defaults.py`)
   - Built-in default values
   - Provides fallback values for all settings
   - Cannot be modified directly

2. **Global Configuration** (`/etc/rtaspi/config.yaml`)
   - System-wide settings
   - Affects all users
   - Requires root access to modify
   - Example: `rtaspi.config.yaml`

3. **User Configuration** (`~/.config/rtaspi/config.yaml`)
   - User-specific settings
   - Overrides global settings
   - Can be modified by the user
   - Example: `user.config.yaml`

4. **Project Configuration** (`.rtaspi/config.yaml`)
   - Project-specific settings
   - Overrides user and global settings
   - Should be version controlled with the project
   - Example: `project.config.yaml`

5. **Environment Variables**
   - Highest precedence
   - Can override any setting
   - Useful for sensitive data (passwords, tokens)
   - Format: `RTASPI_*` (e.g., `RTASPI_LOG_LEVEL=DEBUG`)

## Configuration Files

### Global Configuration (`rtaspi.config.yaml`)
- System-wide default settings
- Basic configuration that works for most cases
- Conservative resource usage
- Default ports and protocols

### User Configuration (`user.config.yaml`)
- Personal preferences
- Development settings
- Custom paths
- Different ports to avoid conflicts
- HTTPS certificates

### Project Configuration (`project.config.yaml`)
- Project-specific devices
- Stream configurations
- Pipeline definitions
- Processing settings
- Local development settings

## Environment Variables

Environment variables can override any configuration value. The mapping is defined in `src/rtaspi/core/defaults.py`. Common variables include:

- `RTASPI_STORAGE_PATH`: Override storage location
- `RTASPI_LOG_LEVEL`: Set logging verbosity
- `RTASPI_WEB_PORT`: Override web interface port
- `RTASPI_TURN_USERNAME`: WebRTC TURN server username
- `RTASPI_TURN_PASSWORD`: WebRTC TURN server password

## Usage Example

1. Install global configuration:
   ```bash
   sudo cp rtaspi.config.yaml /etc/rtaspi/config.yaml
   ```

2. Create user configuration:
   ```bash
   mkdir -p ~/.config/rtaspi
   cp user.config.yaml ~/.config/rtaspi/config.yaml
   ```

3. Initialize project configuration:
   ```bash
   mkdir .rtaspi
   cp project.config.yaml .rtaspi/config.yaml
   ```

4. Set environment variables:
   ```bash
   export RTASPI_LOG_LEVEL=DEBUG
   export RTASPI_TURN_USERNAME=myuser
   export RTASPI_TURN_PASSWORD=mypassword
   ```

## Configuration Validation

All configuration files are validated against schemas defined in:
- `src/rtaspi/schemas/device.py`
- `src/rtaspi/schemas/stream.py`
- `src/rtaspi/schemas/pipeline.py`

These schemas ensure configuration correctness and provide type safety.

## Best Practices

1. Use the most appropriate configuration level:
   - Global: System-wide defaults
   - User: Personal preferences
   - Project: Project-specific settings
   - Environment: Sensitive data

2. Version control:
   - Commit project configuration
   - Ignore user-specific files
   - Never commit sensitive data

3. Use environment variables for:
   - Sensitive information
   - Deployment-specific settings
   - CI/CD configuration

4. Document any custom configuration:
   - What settings were changed
   - Why changes were needed
   - Impact on the system
