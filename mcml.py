name = 'MCML'

# imports
import argparse
import logging
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as xml

log = logging.getLogger(name)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(logging.DEBUG)
fmt = '[{name}][{asctime}][{levelname}]: {message}'
formatter = logging.Formatter(fmt=fmt, datefmt='%S:%M:%H %d-%m-%Y',
                              style='{')
handler.setFormatter(formatter)
log.addHandler(handler)

log.info('Thank you for using %s by TheNetherFTW!', name)

parser = argparse.ArgumentParser()
parser.add_argument('-jar', type=str, default='minecraft_server.jar',
                    help='Minecraft server .jar file')
parser.add_argument('--close-server', '-c', action='store_true',
                    help=('Flag indicating that server should be closed'
                          ' after placing the command blocks'))
parser.add_argument('--files', '-f', nargs='*', default=[],
                    help='Files to be parsed')
settings = parser.parse_args()

# cmd block data:
# 0: -y
# 1: +y
# 2: -z
# 3: +z
# 4: -x
# 5: +x 
# 6: - 
# 7: -
# 8: -y, c
# 9: +y, c
# 10: -z, c
# 11: +z, c
# 12: -x, c
# 13: +x, c

cmd_block_data = {
    '-y': 0, '+y': 1, '-yc': 8, '+yc': 9,
    '-z': 2, '+z': 3, '-zc': 10, '+yc': 11,
    '-x': 4, '+x': 5, '-xc': 12, '+xc': 13,
}
    
setblock = ('/setblock {x} {y} {z} {type}command_block {data} replace '
            '{{Command:"{cmd}",auto:{auto}b}}')


def create_command(cmd, x, y, z, type, conditional, auto):
    global direction
    if '"' in cmd:
        cmd = cmd.replace('"', '\\"')
    if type == 0:
        type = ''
    elif type == 1:
        type = 'chain_'
    elif type == 2:
        type = 'repeating_'
    if conditional:
        data = cmd_block_data[direction + 'c']
    else:
        data = cmd_block_data[direction]
    return setblock.format(x=x, y=y, z=z, type=type,
                           cmd=cmd, data=data, auto=auto)

        
def isolate_tag(name, source, file, error=True):
    start, end = '<{}>'.format(name), '</{}>'.format(name)
    for i, line1 in source:
        if (not line1) or line1.startswith(('#', '//')):
            continue
        break
    try:
        line1
    except UnboundLocalError:
        log.warning('%s: line %s: Reached end of stream.', file, '?')
        return
    if not line1.startswith(start):
        if error:
            log.error('%s: line %r: Excpected "%s" tag.', file, i, start)
        return
    data = []
    if end in line1:
        return enumerate([line1.replace(start, '').replace(end, '').strip()],
                         start=i)
    for r, line in source:
        if line.startswith(end):
            break
        if line and not line.startswith(('#', '//')):
            data.append(line)
    else:
        log.error('%s: line %r: Expected closing tag for tag "%s"',
                  file, r, start)
        return
    return enumerate(data, start=i+1)


def find_coords(block, filename):
    coords = [None, None, None]
    for i, name in enumerate(['x', 'y', 'z']):
        coord = isolate_tag(name, block, filename)
        if coord is None:
            return
        r, coord = next(coord)
        try:
            coord = int(coord)
        except ValueError:
            log.error('%s: line %r: Invalid coordinate: %s',
                      filename, r, coord)
            return
        coords[i] = coord
    return list(coords)


def collect_commands(block, filename):
    impulse = False
    chain = False
    repeating = False
    conditional = False
    auto = False
    placed = 0
    commands = []
    for i, line in block:
        if line.startswith('<'):
            name = line[1:-1]
            if name.startswith('/'):
                name = name[1:]
                def invalid_close(name):
                    msg = ('%s: line %r: closing tag'
                           ' before opening tag ("%s")')
                    log.error(msg, filename, i, name)
                if name == 'impulse':
                    if not impulse:
                        invalid_close('impulse')
                        return
                    impulse = False
                elif name == 'chain':
                    if not chain:
                        invalid_close('chain')
                        return
                    chain = False
                elif name == 'repeating':
                    if not repeating:
                        invalid_close('repeating')
                        return
                    repeating = False
                elif name == 'conditional':
                    if not conditional:
                        invalid_close('conditional')
                        return
                    conditional = False
                elif name == 'auto':
                    if not auto:
                        invalid_close('auto')
                        return
                    auto = False
                else:
                    log.error('%s: line %r: Invalid tag: "%s"', filename, i, name)
                    return
            else:
                if name in {'impulse', 'repeating', 'chain'}:
                    if chain or impulse or repeating:
                        log.error('%s: line %r: Invalid placement of tag "%s"',
                                  filename, i, name)
                        return
                    if name == 'impulse':
                        impulse = True
                    elif name == 'repeating':
                        repeating = True
                    elif name == 'chain':
                        chain = True
                elif name == 'conditional':
                    if conditional:
                        log.error('%s: line %r: Invalid placement of tag "%s"',
                                  filename, i, name)
                        return
                    conditional = True
                elif name == 'auto':
                    if auto:
                        log.error('%s: line %r: Invalid placement of tag "%s"',
                                  filename, i, name)
                        return
                    auto = True
                else:
                    log.error('%s: line %r: Invalid tag: "%s"', filename, i, name)
                    return
        else:
            if impulse:
                type = 0
            elif chain:
                type = 1
            elif repeating:
                type = 2
            elif placed == 0:
                placed = 1
                type = 2
            else:
                type = 1
            commands.append(create_command(line, *coords, type,
                                           conditional, int(auto)))
            if '+x' in direction:
                coords[0] += 1
            if '-x' in direction:
                coords[0] -= 1
            if '+y' in direction:
                coords[1] += 1
            if '-y' in direction:
                coords[1] -= 1
            if '+z' in direction:
                coords[2] += 1
            if '-z' in direction:
                coords[2] -= 1
    return commands

# Repeater data
# 0: -z
# 1: +x
# 2: +z
# 3: -x

repeater_data = {
    '-z': 0,
    'x': 1, '+x': 1,
    'z': 2, '+z': 2,
    '-x': 3
}

def substitute(cmd):
    finder = re.compile(r'\$<[\w]{1,}>')
    extra = []
    while True:
        id_ = finder.search(cmd)
        if id_ is None:
            break
        loc = id_.group()[2:-1]
        if loc not in sections:
            log.error('%s: command %s: Unresolved name binding "%s"',
                      filename, cmd, id_)
            return 
        start, end = id_.span()
        begin = cmd[:start]
        end = cmd[end:]
        crds = sections[loc]
        if direction in {'x', '+x'}:
            crds[0] -= 2
            x, y, z = crds[0] + 1, crds[1], crds[2]
        elif direction == '-x':
            crds[0] += 2
            x, y, z = crds[0] - 1, crds[1], crds[2]
        elif direction in {'z', '+z'}:
            crds[2] -= 2
            x, y, z = crds[0], crds[1], crds[2] + 1
        else:
            crds[2] += 2
            x, y, z = crds[0], crds[1], crds[2] - 1
        cmd = begin + ' '.join([str(crd) for crd in crds]) + end
        extra.append('/setblock {} {} {} stone 6'.format(x, y-1, z))
        extra.append('/setblock {} {} {} unpowered_repeater {}'.format(x, y, z,
                                                        repeater_data[direction]))
    return cmd, extra 


def aboard():
    log.error('Aboarding interpreting of file %s. Skipping file.', filename)


def iterstrip(file):
    for line in file:
        yield line.strip()


def spawn_blocks(*blocks):
    input(('Press enter whenever ready to place the command blocks.'
           ' (The player has to be in the area!)...'))
    print('->')
    for block_array in blocks:
        for command in block_array:
            process.stdin.write(bytes(command + '\n', 'ascii'))
            process.stdin.flush()

            
# Run the server
win_command = 'java -Xms1G -Xmx1G -jar {}'.format(settings.jar)
process = subprocess.Popen(win_command.split(), stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

for filename in settings.files:
    log.info('Interpreting file: %s', filename)
    try:
        with open(filename) as file:
            source = enumerate(iterstrip(file), start=1)
            sections = {}
            log.debug('Isolating start tag...')
            block = isolate_tag('start', source, filename)
            if block is None:
                aboard()
                continue
            log.debug('Getting starting coordinates...')
            coords = find_coords(block, filename)
            if coords is None:
                aboard()
                continue
            original_coords = coords.copy()
            log.info('%s: Found starting coordinates: %s', filename, coords)
            log.debug('Isolating direction tag...')
            direction = isolate_tag('direction', source, filename)
            if direction is None:
                aboard()
                continue
            i, direction = next(direction)
            if direction not in {'x', '+x', '-x', 'z', '+z', '-z'}:
                log.error('%s: line %r: Invalid direction: %s',
                          filename, i, direction)
                aboard()
                continue
            if not direction.startswith(('+', '-')):
                direction = '+' + direction
            log.info('%s: Found block direction: %s', filename, direction)
            headers = [[], [], [], [], []]
            it = enumerate(['setup', 'teardown', 'spawning', 'startup', 'reset'])
            crds = original_coords.copy()
            for index, header in it:
                log.debug('Isolating %s tag...', header)
                block = isolate_tag(header, source, filename)
                if block is None:
                    aboard()
                    continue
                log.debug('Parsing %s tag...', header)
                headers[index] = collect_commands(block, filename)
                if headers[index] is None:
                    aboard()
                    continue
                sections[index] = crds.copy()
                crds[1] += 2
                coords = crds.copy()
            log.debug('Isolating blocks tag...')
            block = isolate_tag('blocks', source, filename)
            if block is None:
                aboard()
                continue
            log.debug('Isolating new start tag...')
            start = isolate_tag('start', block, filename)
            if start is None:
                aboard
                continue
            log.debug('Isolating relative tag...')
            rel = isolate_tag('relative', start, filename)
            if rel is None:
                aboard()
                continue
            i, rel = next(rel)
            try:
                rel = bool(int(rel))
            except ValueError:
                log.error('%s: line %r: Invalid value for "relative" tag: %s',
                          filename, i, rel)
            log.debug('Getting relative starting coordinates...')
            coords = find_coords(start, filename)
            if coords is None:
                aboard()
                continue
            dx, dy, dz = coords
            if rel:
                x, y, z = original_coords
                start_coords = [x + dx, y + dy, z + dz]
            else:
                start_coords = [dx, dy, dz]
            prev_coords = start_coords.copy()
            commands = []
            error = False
            while True:
                log.debug('Isolating section...')
                section = isolate_tag('section', block, filename)
                if section is None:
                    log.info(('%s: Could not find a new block section.'
                              ' Considering file interpreted.'), filename)
                    break
                log.debug('Isolating name...')
                section_name = isolate_tag('name', section, filename)
                if section_name is None:
                    error = True
                    break
                _, section_name = next(section_name)
                log.debug('Isolating section start tag...')
                start = isolate_tag('start', section, filename)
                if start is None:
                    error = True
                    break
                log.debug('Isolating relative tag...')
                rel = isolate_tag('relative', start, filename)
                if rel is None:
                    error = True
                    break
                i, rel = next(rel)
                try:
                    rel = bool(int(rel))
                except ValueError:
                    log.error('%s: line %r: Invalid value for "relative" tag: %s',
                              filename, i, rel)
                    error = True
                    break
                log.debug('Getting section relative coordinates...')
                coords = find_coords(start, filename)
                if coords is None:
                    error = True
                    break
                dx, dy, dz = coords
                if rel:
                    x, y, z = prev_coords
                    coords = [x + dx, y + dy, z + dz]
                else:
                    x, y, z = start_coords
                    coords = [x + dx, y + dy, z + dz]
                prev_coords = coords.copy()
                log.info('Found section "%s" at %s', section_name, coords)
                log.debug('Collecting commands...')
                block_section = collect_commands(section, filename)
                sections[section_name] = prev_coords.copy()
                commands.extend(block_section)
            if error:
                aboard()
                continue
            log.info('Applying name bindings...')
            error = False
            extra_commands = []
            tot_commands = headers + [commands]
            for array in tot_commands:
                for i, cmd in enumerate(array[:]):
                    cmd = substitute(cmd)
                    if cmd is None:
                        error = True
                        break
                    cmd, extra = cmd
                    extra_commands.extend(extra)
                    array[i] = cmd
                if error:
                    aboard()
                    continue
            log.info('Done interpreting file %s', filename)
            log.info('Command output:')
            it = zip(tot_commands + [extra_commands],
                     ['setup', 'teardown', 'spawning', 'startup',
                      'reset', 'commands', 'extra'])
            for array, name in it:
                log.info('%s:', name)
                for cmd in array:
                    log.info(cmd)
            log.info('----------------------------------------')
            spawn_blocks(*headers, commands, extra_commands)
    except FileNotFoundError:
        log.error('Cannot find file: %s. Skipping file', filename)
    except OSError as e:
        log.error('Unexpected error: %s. Skipping file', e)
    except Exception as e:
        log.critical('Unxcpected fatal error: %s. Shutdown.', e)
        raise 

log.info('Done!')
if settings.close_server:    
    log.info('Stopping server...')
    process.stdin.write(b'stop\n')
    process.stdin.flush()
log.info('Thank you for using %s by TheNetherFTW', name)
