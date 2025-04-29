#compdef rtaspi

# ZSH completion for rtaspi

_rtaspi() {
    local curcontext="$curcontext" state line
    typeset -A opt_args

    local -a commands
    commands=(
        'config:Manage rtaspi configuration'
        'devices:Manage audio/video devices'
        'streams:Manage audio/video streams'
        'pipelines:Manage processing pipelines'
        'server:Manage web server'
        'version:Show version information'
        'completion:Generate shell completion script'
    )

    local -a global_options
    global_options=(
        '(-c --config)'{-c,--config}'[Path to configuration file]:config file:_files -g "*.yaml"'
        '(-v --verbose)'{-v,--verbose}'[Enable verbose logging]'
        '(-h --help)'{-h,--help}'[Show help message]'
    )

    _arguments -C \
        $global_options \
        '1: :->command' \
        '*:: :->args' && return 0

    case $state in
        command)
            _describe -t commands 'rtaspi commands' commands
            ;;
        args)
            case $words[1] in
                config)
                    local -a config_commands
                    config_commands=(
                        'get:Get configuration value(s)'
                        'set:Set configuration value'
                        'unset:Remove configuration value'
                        'dump:Dump complete configuration to file'
                        'load:Load configuration from file(s)'
                    )
                    _arguments \
                        '1: :->subcommand' \
                        '*:: :->config_args'

                    case $state in
                        subcommand)
                            _describe -t config_commands 'config commands' config_commands
                            ;;
                        config_args)
                            case $words[1] in
                                load)
                                    _files -g "*.yaml"
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
                devices)
                    local -a devices_commands device_types
                    devices_commands=(
                        'list:List configured devices'
                        'add:Add a new device'
                        'remove:Remove a device'
                        'show:Show device details'
                        'set:Set device configuration value'
                        'status:Show device status'
                        'scan:Scan device capabilities'
                    )
                    device_types=(
                        'USB_CAMERA' 'BUILT_IN_CAMERA' 'CSI_CAMERA'
                        'USB_MICROPHONE' 'BUILT_IN_MICROPHONE'
                        'IP_CAMERA' 'ONVIF_CAMERA' 'RTSP_CAMERA'
                        'NETWORK_MICROPHONE' 'VOIP_DEVICE'
                        'VIRTUAL_CAMERA' 'VIRTUAL_MICROPHONE'
                        'SCREEN_CAPTURE' 'AUDIO_LOOPBACK'
                    )
                    _arguments \
                        '1: :->subcommand' \
                        '*:: :->device_args'

                    case $state in
                        subcommand)
                            _describe -t devices_commands 'devices commands' devices_commands
                            ;;
                        device_args)
                            case $words[1] in
                                list|show|status)
                                    _arguments \
                                        '--type=[Filter by device type]:device type:($device_types)' \
                                        '--format=[Output format]:(table yaml json)'
                                    ;;
                                add)
                                    _arguments \
                                        '--type=[Device type]:device type:($device_types)' \
                                        '--settings=[Device settings file]:settings file:_files -g "*.yaml"'
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
                streams)
                    local -a streams_commands stream_types
                    streams_commands=(
                        'list:List configured streams'
                        'create:Create a new stream'
                        'remove:Remove a stream'
                        'show:Show stream details'
                        'set:Set stream configuration value'
                        'status:Show stream status'
                        'start:Start a stream'
                        'stop:Stop a stream'
                        'restart:Restart a stream'
                    )
                    stream_types=('video' 'audio' 'both')
                    _arguments \
                        '1: :->subcommand' \
                        '*:: :->stream_args'

                    case $state in
                        subcommand)
                            _describe -t streams_commands 'streams commands' streams_commands
                            ;;
                        stream_args)
                            case $words[1] in
                                list|show|status)
                                    _arguments \
                                        '--type=[Filter by stream type]:stream type:($stream_types)' \
                                        '--format=[Output format]:(table yaml json)'
                                    ;;
                                create)
                                    _arguments \
                                        '--type=[Stream type]:stream type:($stream_types)' \
                                        '--settings=[Stream settings file]:settings file:_files -g "*.yaml"'
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
                pipelines)
                    local -a pipelines_commands stage_types
                    pipelines_commands=(
                        'list:List configured pipelines'
                        'create:Create a new pipeline'
                        'add-stage:Add a stage to a pipeline'
                        'remove-stage:Remove a stage from a pipeline'
                        'remove:Remove a pipeline'
                        'show:Show pipeline details'
                        'status:Show pipeline status'
                        'start:Start a pipeline'
                        'stop:Stop a pipeline'
                        'validate:Validate a pipeline configuration'
                    )
                    stage_types=('source' 'filter' 'transform' 'merge' 'split' 'output')
                    _arguments \
                        '1: :->subcommand' \
                        '*:: :->pipeline_args'

                    case $state in
                        subcommand)
                            _describe -t pipelines_commands 'pipelines commands' pipelines_commands
                            ;;
                        pipeline_args)
                            case $words[1] in
                                list|show|status)
                                    _arguments '--format=[Output format]:(table yaml json)'
                                    ;;
                                create)
                                    _arguments \
                                        '--settings=[Pipeline settings file]:settings file:_files -g "*.yaml"'
                                    ;;
                                add-stage)
                                    _arguments '--type=[Stage type]:stage type:($stage_types)'
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
                server)
                    local -a server_commands
                    server_commands=(
                        'start:Start the web server'
                        'stop:Stop the web server'
                        'status:Show server status'
                        'config:Show server configuration'
                        'openapi:Generate OpenAPI documentation'
                        'generate-cert:Generate SSL certificate'
                        'create-admin:Create admin user'
                        'reset-password:Reset admin user password'
                        'api-token:Manage API tokens'
                        'create-token:Create new API token'
                        'revoke-token:Revoke API token'
                    )
                    _arguments \
                        '1: :->subcommand' \
                        '*:: :->server_args'

                    case $state in
                        subcommand)
                            _describe -t server_commands 'server commands' server_commands
                            ;;
                        server_args)
                            case $words[1] in
                                start)
                                    _arguments \
                                        '--host=[Host to bind to]' \
                                        '--port=[Port to listen on]' \
                                        '--ssl[Enable HTTPS]' \
                                        '--cert=[SSL certificate file]:certificate:_files -g "*.{pem,crt}"' \
                                        '--key=[SSL private key file]:key:_files -g "*.{pem,key}"'
                                    ;;
                                config|openapi)
                                    _arguments '--format=[Output format]:(yaml json)'
                                    ;;
                            esac
                            ;;
                    esac
                    ;;
                completion)
                    _arguments '--shell=[Shell type]:(bash zsh fish)'
                    ;;
            esac
            ;;
    esac
}

_rtaspi "$@"
