#!/usr/bin/env bash

_rtaspi_completion() {
    local cur prev words cword
    _init_completion || return

    # Get all commands from rtaspi --help
    local commands="config devices streams pipelines server version completion"
    
    # Get all options that work with every command
    local global_options="--config -c --verbose -v --help -h"
    
    # Handle command completion
    if [[ $cword == 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    # Get the command (e.g. 'config', 'devices', etc.)
    local command=${words[1]}

    case $command in
        config)
            local subcommands="get set unset dump load"
            if [[ $cword == 2 ]]; then
                COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
            elif [[ $prev == "load" ]]; then
                _filedir yaml
            fi
            ;;
        devices)
            local subcommands="list add remove show set status scan"
            if [[ $cword == 2 ]]; then
                COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
            elif [[ $prev == "--type" ]]; then
                local types="USB_CAMERA BUILT_IN_CAMERA CSI_CAMERA USB_MICROPHONE BUILT_IN_MICROPHONE IP_CAMERA ONVIF_CAMERA RTSP_CAMERA NETWORK_MICROPHONE VOIP_DEVICE VIRTUAL_CAMERA VIRTUAL_MICROPHONE SCREEN_CAPTURE AUDIO_LOOPBACK"
                COMPREPLY=( $(compgen -W "$types" -- "$cur") )
            elif [[ $prev == "--format" ]]; then
                COMPREPLY=( $(compgen -W "table yaml json" -- "$cur") )
            fi
            ;;
        streams)
            local subcommands="list create remove show set status start stop restart"
            if [[ $cword == 2 ]]; then
                COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
            elif [[ $prev == "--type" ]]; then
                COMPREPLY=( $(compgen -W "video audio both" -- "$cur") )
            elif [[ $prev == "--format" ]]; then
                COMPREPLY=( $(compgen -W "table yaml json" -- "$cur") )
            fi
            ;;
        pipelines)
            local subcommands="list create add-stage remove-stage remove show status start stop validate"
            if [[ $cword == 2 ]]; then
                COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
            elif [[ $prev == "--type" ]]; then
                COMPREPLY=( $(compgen -W "source filter transform merge split output" -- "$cur") )
            elif [[ $prev == "--format" ]]; then
                COMPREPLY=( $(compgen -W "table yaml json" -- "$cur") )
            fi
            ;;
        server)
            local subcommands="start stop status config openapi generate-cert create-admin reset-password api-token create-token revoke-token"
            if [[ $cword == 2 ]]; then
                COMPREPLY=( $(compgen -W "$subcommands" -- "$cur") )
            elif [[ $prev == "--format" ]]; then
                COMPREPLY=( $(compgen -W "yaml json" -- "$cur") )
            elif [[ $prev == "--shell" ]]; then
                COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") )
            fi
            ;;
        completion)
            if [[ $prev == "--shell" ]]; then
                COMPREPLY=( $(compgen -W "bash zsh fish" -- "$cur") )
            fi
            ;;
    esac

    # Handle global options
    if [[ $cur == -* ]]; then
        COMPREPLY=( $(compgen -W "$global_options" -- "$cur") )
    fi

    return 0
}

complete -F _rtaspi_completion rtaspi
