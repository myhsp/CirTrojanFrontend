import os
import sys
import base64
import winreg
import traceback
import subprocess
from copy import deepcopy

from github import Github
import time


class GitMan:

    def git_connect(self, uname='myhsp'):
        self.uname = uname
        self.session = Github(self.token)
        self.git = self.session.get_repo(self.repo)
        self.issue = self.git.get_issues()[0]

    def git_fetch_latest_comment(self, check_is_bot=True) -> tuple:
        latest_comment = self.issue.get_comments().reversed[0]
        return (latest_comment.user, latest_comment.body) if (latest_comment.body[0] != '>' or not check_is_bot) else (
            None, None)

    def git_commit_comment(self, content):
        self.issue.create_comment(body=str(content))

    def get_file_content(self, module_name):
        return base64.b64decode(self.git.get_contents('{}.py'.format(module_name)).content).decode(encoding='utf-8')

    def __init__(self):
        self.session = None
        self.git = None
        self.issue = None
        self.token = None
        self.uname = None
        self.repo = None
        self.expires = None

        with open('./token.txt') as f:
            self.token, self.repo, self.expires = f.readline().strip().split(' ')
            f.close()

        self.git_connect()


class Process:
    def __init__(self, command):
        self.environment_path = self.get_environment_path()
        self.process = subprocess.Popen(command.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, universal_newlines=True, env=os.environ)

    def get_output(self, print_char):
        output = ""
        while True:
            char = self._read_char()
            if print_char:
                print(char, end="")
            output += char
            if char == '>' or char == '?' or char == '$' or char == 'END':
                return output

    def input_text(self, text):
        if text == 'DONOTHING':
            return
        self.process.stdin.write("{}\n".format(text))
        self.process.stdin.flush()

    def _read_char(self):
        char = self.process.stdout.read(1)
        if not char:
            return 'END'
        else:
            return char

    def get_environment_path(self):
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
        path_value = winreg.QueryValueEx(key, "Path")[0]
        os.environ['Path'] = path_value
        winreg.CloseKey(key)
        return path_value


class ContentRenderer:
    class NoticeType:
        INFO = 0
        FATAL = 1
        WARNING = 2

        NOTICE_ICON = {
            INFO: '[INFO]',
            FATAL: '[FATAL]',
            WARNING: '[WARNING]'
        }

    def __init__(self):
        pass


def render_reference(content):
    return '> {}\n'.format(content)


def render_notice(content,
                  notice_type=ContentRenderer.NoticeType.INFO,
                  t=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())):
    return '**{}** [{}] {}'.format(ContentRenderer.NoticeType.NOTICE_ICON[notice_type], t, content)


def render_tabel(self, header: tuple, sequence: list[tuple]):
    header_column_template = '<th>{}</th>'
    column_template = '<td>{}</td>'

    line_template = '<tr>{}</tr>'
    table_template = '<table>{}</table>'

    header_content = ''
    for i in header:
        header_content += header_column_template.format(str(i))
    header = line_template.format(header_content)

    lines = ''
    for l in sequence:
        line = ''
        for c in l:
            line += column_template.format(str(c))
        lines += line_template.format(line)
    table = table_template.format(header + lines)

    return table


def render_list(content: list):
    l = ''
    for i in content:
        l += '- {}\n'.format(str(i))
    l += '\n'
    return l


'''
check_is_python_extension = lambda body: True if body.split('\n')[0].strip()[0] == '#' \
                                                 and 'python-extension' in body.split('\n')[0] else False
'''


class CommandParserType:
    CMD_INTERNAL = 0
    CMD_SHELL = 1
    CMD_RUN_MODULE = 2
    CMD_LOAD_MODULE = 3
    CMD_LOAD_CONFIG = 4


def command_parser(command: str):
    sequence = command.split('\n')
    header = sequence[0]

    if 'internal' in header:
        return CommandParserType.CMD_INTERNAL
    elif 'load_module' in header:
        return CommandParserType.CMD_LOAD_MODULE
    elif 'run_module' in header:
        return CommandParserType.CMD_RUN_MODULE
    elif 'load_config' in header:
        return CommandParserType.CMD_LOAD_CONFIG
    else:
        return CommandParserType.CMD_SHELL


def config_parser(config: list) -> dict[str, list]:
    ret = {}
    for l in config:
        l = l.strip()
        if len(l.split(' ')) > 1:
            e = l.split(' ')[1].split(';')
        else:
            e = None
        ret.update(deepcopy({l.split(' ')[0]: deepcopy(e)}))
    return ret


class Control:
    def __init__(self, git: GitMan, interval=30):
        self.update_interval = interval

        self.current_folder = os.getcwd()
        self.config = None

        self.git = git

        self.proc = Process("powershell")

    def exec_cmd(self, cmd):
        os.popen('cd {}&&{}'.format(self.current_folder, cmd), 'r')
        return 'Success!'

    def exec_internal_cmd(self, cmd_name, *args):
        ret = self.__getattribute__(cmd_name)(*args)
        return ret

    def get_folder_content(self):
        return os.listdir(self.current_folder)

    def get_folder_content_rendered(self):
        content = self.get_folder_content()
        l = '\n' + render_list(content)
        return l

    def get_all_methods_rendered(self):
        content = self.__dir__()
        l = '\n' + render_list(content)
        return l

    def set_current_folder(self, folder):
        if os.path.exists(folder):
            self.current_folder = folder
        return self.current_folder

    def move_backward(self):
        upper_level = '\\'.join(self.current_folder.split('\n')[0:-1])
        if os.path.exists(upper_level):
            self.current_folder = upper_level
        return self.current_folder

    def get_config(self):
        if os.path.exists(os.getcwd() + '\\config.conf'):
            with open(os.getcwd() + '\\config.conf', 'r', encoding='utf-8') as f:
                f.seek(0, 0)
                if '#null' in f.readline():
                    self.config = {}
                else:
                    self.config = config_parser(f.readlines())
                f.close()
        else:
            with open(os.getcwd() + '\\config.conf', 'w') as f:
                f.write('#null')
                f.flush()
                f.close()

    def set_config(self, config: str):
        self.config = config_parser(config.split('\n'))
        with open(os.getcwd() + '\\config.conf', 'w') as f:
            f.write(config)
            f.close()

        self.get_config()

    def install_pip_package(self, pakages: str):
        mirror = 'https://pypi.tuna.tsinghua.edu.cn/simple'
        cmd = 'pip install -i {} {}'.format(mirror, ' '.join(pakages.split(';')))

        with open('./pip_loader.cmd', 'w') as f:
            f.write(cmd)
            f.close()

        ret = self.exec_cmd('start {}\\pip_loader.py'.format(os.getcwd()))
        return ret

    def load_package(self):
        packages = []
        pip_packages = []
        for i in self.config:
            packages.append(i)
            for c in self.config[i]:
                if c not in pip_packages and c is not None:
                    pip_packages.append(c)

        for p in packages:
            if p not in sys.modules:
                exec('import extension.{}'.format(p))

        pip_packages_need_install = []
        for p in pip_packages:
            try:
                exec('import {}'.format(p))
            except:
                pip_packages_need_install.append(p)

        if len(pip_packages_need_install) != 0:
            self.install_pip_package(';'.join(pip_packages_need_install))

    def init_module(self, module_name, module_body):
        if not os.path.exists(os.getcwd() + '\\extension'):
            os.mkdir(os.getcwd() + '\\extension')

        with open('{}\\extension\\{}.py'.format(os.getcwd(), module_name), 'w', encoding='utf-8') as f:
            f.write(module_body)
            f.close()

    def run_module(self, name, *args):
        if name not in sys.modules:
            exec('import extension.{}'.format(name))
        ret = sys.modules['extension.{}'.format(name)].run(*args)
        return ret

    def update_token(self, token, repo, expires):
        with open('./token.txt', 'w', encoding='utf-8') as f:
            f.write('{} {} {}'.format(token, repo, expires))
            f.close()

    def start(self):
        self.get_config()
        self.load_package()

        self.git.git_commit_comment('> The token will expire on **{}**'.format(self.git.expires))

        while 1:
            msg = ''
            try:

                msg = self.git.git_fetch_latest_comment()[1]

                if msg is not None:
                    cmd_type = command_parser(msg)
                    r = ''
                    if cmd_type == CommandParserType.CMD_INTERNAL:
                        '''
                        internal
                        <internal method name> [arg1] ...
                        '''
                        sequence = msg.split('\n')[1:]
                        for i in sequence:
                            func_name = i.split(' ')[0]
                            args = i.split(' ')[1:]

                            r += render_notice(self.exec_internal_cmd(func_name, *args),
                                               ContentRenderer.NoticeType.INFO) + '\n'

                    elif cmd_type == CommandParserType.CMD_SHELL:
                        '''
                        <shell command>
                        '''
                        # self.exec_cmd('&&'.join(msg.strip().split('\n')))

                        self.proc.input_text('&&'.join(msg.strip().split('\n')))
                        cmdline_ret = self.proc.get_output(print_char=False)

                        r = render_notice('\n{}'.format(cmdline_ret),
                                          ContentRenderer.NoticeType.INFO)

                    elif cmd_type == CommandParserType.CMD_RUN_MODULE:
                        '''
                        run_module
                        <module name> [arg] ...
                        
                        module must have a run(*args) method / function. 
                        '''
                        sequence = msg.split('\n')[1:]

                        for s in sequence:
                            name = s.split(' ')[0]
                            args = []
                            if len(s.split(' ')) > 1:
                                args = s.split(' ')[1:]
                            if name in sys.modules:
                                r += render_notice(self.run_module(name, *args),
                                                   ContentRenderer.NoticeType.INFO) + '\n'
                            else:
                                try:
                                    exec('import extension.{}'.format(name))
                                    r += render_notice(self.run_module(name, *args),
                                                       ContentRenderer.NoticeType.INFO) + '\n'
                                except:
                                    r += render_notice('Module not found.', ContentRenderer.NoticeType.FATAL)

                    elif cmd_type == CommandParserType.CMD_LOAD_CONFIG:
                        '''
                        load_config
                        <config: <module name> <dependency 1>;<dependency 2>;...
                        '''
                        conf = '\n'.join(msg.split('\n')[1:])
                        self.set_config(conf)

                        r += render_notice('Config successfully updated.', ContentRenderer.NoticeType.INFO) + '\n'

                    elif cmd_type == CommandParserType.CMD_LOAD_MODULE:
                        '''
                        load_module
                        <name>
                        <module content>
                        '''
                        sequence = msg.split('\n')[1:]

                        name = sequence[0]
                        body = self.git.get_file_content(name)  # '\n'.join(sequence[1:])

                        self.init_module(name, body)

                        r += render_notice('Module successfully loaded.', ContentRenderer.NoticeType.INFO) + '\n'

                    r = '> {}\n\n{}'.format(msg, r)
                    self.git.git_commit_comment(r)
            except Exception as e:
                tb = traceback.format_exc()
                self.git.git_commit_comment('> {}\n\n{}\n{}' \
                                            .format(msg, render_notice('Program crashed while executing!',
                                                                       ContentRenderer.NoticeType.FATAL), tb)
                                            )
            time.sleep(self.update_interval)
            print('a new loop...')


if __name__ == '__main__':
    git = GitMan()
    control = Control(git, interval=30)

    control.start()
