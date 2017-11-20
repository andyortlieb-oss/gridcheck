import argparse
import json
import logging
import sys
import os

from collections import defaultdict

logger = logging.getLogger(__name__)


def get_environ_maps(arg_parser, env_prefix):
    env_arg_map = {}
    arg_env_map = defaultdict(list)
    for action in arg_parser._actions:
        for name in action.option_strings:
            # Convert the name to an env name, Ex: --local-ip becomes LOCAL_IP
            name = name.strip('-').upper().replace('-', '_')

            if name in env_arg_map:
                raise Exception("Application error: Duplicate environment settings names discovered for %s" % name)
            if len(name) > 1:
                # Map the env name to the first
                env_key = '%s%s' % (env_prefix, name)
                env_arg_map[env_key] = action
                arg_env_map[action.option_strings[0]].append(env_key)
            else:
                pass  # Do nothing with 1 char args.
    return env_arg_map, arg_env_map


def get_args_from_env(arg_parser, arg_source, env_source, env_prefix):
    new_arg_source_dict = {}
    new_arg_source_list = []

    env_arg_map, arg_env_map = get_environ_maps(arg_parser, env_prefix)

    # Look at the environment for keys that can map to args.
    for env_key, env_val in env_source.items():
        # Determine the arg_key this will map to.
        arg_key_action = env_arg_map.get(env_key)

        # If it doesn't exist, we don't care about it.
        if not arg_key_action:
            continue
        else:
            pass
        # Reassign to the first argument that it will be mapped to.
        arg_key = arg_key_action.option_strings[0]

        # If we've already set this arg_key and the values don't match, it's a conflict
        if arg_key in new_arg_source_dict and new_arg_source_dict[arg_key] != env_val:
            raise Exception('Conflicting environment key %s' % env_key)

        # Make sure this setting isn't already set by cli arguments, which take priority.
        conflict = set(arg_key_action.option_strings).intersection(set(arg_source))
        if len(conflict):
            logger.warning("Discarding environment variable `%s` which conflicts with cli argument `%s`" % (
                           env_key, '|'.join(conflict)))
        else:
            new_arg_source_dict[arg_key] = env_val

    # Convert the dictionary into a flattened list.
    # FIXME : What can we do to detect for lists and explode them into multi args?
    for env_key, env_val in new_arg_source_dict.items():
        new_arg_source_list += [env_key, env_val]

    return arg_source + new_arg_source_list


def get_args(sysargs=sys.argv[1:], environ=os.environ):
    parser = argparse.ArgumentParser(description='Gridcheck')
    parser.add_argument(
        '--seed-host', '-s',
        type=str, required=True, action='append',
        help='A list of gridcheck base URLs that this process should join.')
    parser.add_argument(
        '--address-source-method', '-M',
        default='settings',
        type=str,
        help='The method gridcheck will use to determine how to publicize this host address.')
    parser.add_argument(
        '--log-tcp-json', '-J',
        type=str, required=False,
        help='Host:port for server accepting TCP JSON Lines'
    )

    # Even though we require all these things to be set, we check for that later on.
    parser.add_argument('--local-ip', default='127.0.0.1')
    parser.add_argument('--local-port', default=1180, type=int)
    parser.add_argument('--local-hostname', default='localhost')
    parser.add_argument('--routable-ip')
    parser.add_argument('--routable-port')
    parser.add_argument('--routable-hostname')

    parser.add_argument('--check-config', action='store_true', default=False,
                        help="Don't start a server, just check and print settings")

    # Load in the settings
    args = parser.parse_args(get_args_from_env(parser, sysargs, environ, 'GRIDCHECK_'))

    # Figure out how to find our local and routable addresses.
    if args.address_source_method == 'settings':
        pass  # Expect everything to be filled in already.
    else:
        args.error("Address source map cannot be `%s`, must be one of settings|mesos/marathon",
                   args.address_source_method)

    #  Just double check that all addressing stuff is really here.
    errors = []
    for k in ['local_ip', 'local_hostname', 'local_port', 'routable_ip', 'routable_hostname', 'routable_port']:
        if not getattr(args, k):
            errors.append("Could not determine %s" % k)

    # If we've accrued any errors, then bail.
    if errors:
        parser.error("\n".join(errors))

    return args


def main(is_main):
    if is_main not in [True, '__main__']:
        return

    args = get_args()

    if args.check_config:
        print(args)


main(__name__)
