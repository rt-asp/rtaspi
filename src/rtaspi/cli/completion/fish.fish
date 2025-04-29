# Fish shell completion for rtaspi

# Define all commands
set -l commands config devices streams pipelines server version completion

# Define global options
set -l global_options --config -c --verbose -v --help -h

# Command-specific completions
complete -c rtaspi -n "not __fish_seen_subcommand_from $commands" -a "$commands"
complete -c rtaspi -n "not __fish_seen_subcommand_from $commands" -l help -s h -d "Show help message"
complete -c rtaspi -n "not __fish_seen_subcommand_from $commands" -l config -s c -d "Path to configuration file"
complete -c rtaspi -n "not __fish_seen_subcommand_from $commands" -l verbose -s v -d "Enable verbose logging"

# Config command completions
set -l config_commands get set unset dump load
complete -c rtaspi -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $config_commands" -a "$config_commands"

# Devices command completions
set -l devices_commands list add remove show set status scan
set -l device_types USB_CAMERA BUILT_IN_CAMERA CSI_CAMERA USB_MICROPHONE BUILT_IN_MICROPHONE IP_CAMERA ONVIF_CAMERA RTSP_CAMERA NETWORK_MICROPHONE VOIP_DEVICE VIRTUAL_CAMERA VIRTUAL_MICROPHONE SCREEN_CAPTURE AUDIO_LOOPBACK
complete -c rtaspi -n "__fish_seen_subcommand_from devices; and not __fish_seen_subcommand_from $devices_commands" -a "$devices_commands"
complete -c rtaspi -n "__fish_seen_subcommand_from devices" -l type -a "$device_types"
complete -c rtaspi -n "__fish_seen_subcommand_from devices" -l format -a "table yaml json"

# Streams command completions
set -l streams_commands list create remove show set status start stop restart
set -l stream_types video audio both
complete -c rtaspi -n "__fish_seen_subcommand_from streams; and not __fish_seen_subcommand_from $streams_commands" -a "$streams_commands"
complete -c rtaspi -n "__fish_seen_subcommand_from streams" -l type -a "$stream_types"
complete -c rtaspi -n "__fish_seen_subcommand_from streams" -l format -a "table yaml json"

# Pipelines command completions
set -l pipelines_commands list create add-stage remove-stage remove show status start stop validate
set -l stage_types source filter transform merge split output
complete -c rtaspi -n "__fish_seen_subcommand_from pipelines; and not __fish_seen_subcommand_from $pipelines_commands" -a "$pipelines_commands"
complete -c rtaspi -n "__fish_seen_subcommand_from pipelines" -l type -a "$stage_types"
complete -c rtaspi -n "__fish_seen_subcommand_from pipelines" -l format -a "table yaml json"

# Server command completions
set -l server_commands start stop status config openapi generate-cert create-admin reset-password api-token create-token revoke-token
complete -c rtaspi -n "__fish_seen_subcommand_from server; and not __fish_seen_subcommand_from $server_commands" -a "$server_commands"
complete -c rtaspi -n "__fish_seen_subcommand_from server" -l format -a "yaml json"

# Completion command completions
complete -c rtaspi -n "__fish_seen_subcommand_from completion" -l shell -a "bash zsh fish"

# File completions for relevant options
complete -c rtaspi -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from load" -r -a "*.yaml"
complete -c rtaspi -n "__fish_seen_subcommand_from devices; and __fish_seen_subcommand_from add" -l settings -r -a "*.yaml"
complete -c rtaspi -n "__fish_seen_subcommand_from streams; and __fish_seen_subcommand_from create" -l settings -r -a "*.yaml"
complete -c rtaspi -n "__fish_seen_subcommand_from pipelines; and __fish_seen_subcommand_from create" -l settings -r -a "*.yaml"
complete -c rtaspi -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from start" -l cert -r -a "*.pem *.crt"
complete -c rtaspi -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from start" -l key -r -a "*.pem *.key"
