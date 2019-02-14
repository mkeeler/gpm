#!/usr/bin/env python
import subprocess
import contextlib
import os
import sys
import shutil
import tempfile
import threading
import signal
import time

abspath = lambda x: os.path.abspath(os.path.expandvars(os.path.expanduser(x)))

def which(program):
   def is_exe(fpath):
      return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

   fpath, fname = os.path.split(program)
   if fpath:
      if is_exe(program):
         return program
   else:
      for path in os.environ["PATH"].split(os.pathsep):
         exe_file = os.path.join(path, program)
         if is_exe(exe_file):
            return exe_file

   return None

def bindmount(src, dest):
   bindfs = which('bindfs')
   mount = which('mount')

   if sys.platform == 'darwin' and bindfs is not None:
      subprocess.check_call([bindfs, '-o', 'local,extended_security', src, dest])
      return False
   elif sys.platform.startswith('linux') and bindfs is not None:
      subprocess.check_call([bindfs, '-n', src, dest])
      return True
   elif sys.platform.startswith('linux') and mout is not None:
      subprocess.check_call([mount, '-o', 'bind', src, dest])
      return False
   else:
      raise Exception('Unsupported Platform: darwin/bindfs, linux/bindfs or linux/mount -o bind')

def unbindmount(dest, fusermount_umount):
   fusermount = which('fusermount')
   umount = which('umount')

   for i in range(5):
      try:
         if fusermount is not None:
            subprocess.check_output([fusermount, '-u', dest], stderr=subprocess.STDOUT)
         elif umount is not None:
            subprocess.check_output([umount, dest], stderr=subprocess.STDOUT)
         else:
            raise Exception("Failed to unmount")
      except subprocess.CalledProcessError as e:
         if "Resource busy" not in e.output:
            raise
      else:
         break

      time.sleep(1)

@contextlib.contextmanager
def bindmount_ctx(src, dest):
   fusermount_umount = bindmount(src, dest)
   yield
   unbindmount(dest, fusermount_umount)

def exec_with_bindmount(src, dest, command, working_dir, env):
   done = threading.Event()
   def handler(signum, frame):
      done.set()
   signal.signal(signal.SIGINT, handler)

   with bindmount_ctx(src, dest):
      proc = subprocess.Popen(command, shell=False, cwd=working_dir, env=env)

      while not done.is_set():
         if proc.poll() is not None:
            return proc.returncode
         time.sleep(1)

      if proc.poll() is not None:
         proc.terminate()
      return 0

if __name__ == '__main__':
   import argparse

   def do_mount(args):
      try:
         if args.manage_dir:
            os.makedirs(args.destination)
         bindmount(args.source, args.destination)
      except subprocess.CalledProcessError as e:
         sys.stderr.write('Failed to bind mount: {0}\n'.format(e))
         sys.exit(1)
      else:
         sys.exit(0)

   def do_umount(args):
      try:
         unbindmount(args.path)
         if args.manage_dir:
            shutil.rmtree(args.path)
      except subprocess.CalledProcessError as e:
         sys.stderr.write('Failed to unbind: {0}\n'.format(e))
         sys.exit(1)
      else:
         sys.exit(0)

   @contextlib.contextmanager
   def dir_manage_ctx(manage, path) :
      if manage:
         os.makedirs(path)
      yield
      if manage:
         shutil.rmtree(path)

   @contextlib.contextmanager
   def tempdir_ctx(prefix):
      path = tempfile.mkdtemp(prefix=prefix)
      yield path
      shutil.rmtree(path)

   def do_exec(args):
      try:
         with dir_manage_ctx(args.manage_dir, args.destination):
            command = []
            command.append(which(args.command))
            command.extend(args.args)
            ret = exec_with_bindmount(args.source, args.destination, command, args.wdir, None)
      except subprocess.CalledProcessError as e:
         sys.stderr.write('Failed bind mount: {0}'.format(e))
         sys.exit(1)
      except Exception as e:
         sys.stderr.write('Failed to execute command: {0}'.format(e))
         sys.exit(1)
      except KeyboardInterrupt:
         sys.exit(2)
      else:
         sys.exit(ret)

      sys.exit(0)


   def do_gpm(args):
      try:
         with tempdir_ctx(os.path.basename(args.source)) as tempdir:
            src_path = os.path.join(tempdir, "src", args.package)
            os.makedirs(src_path)
            go_path = ':'.join([tempdir,os.environ["GOPATH"]])
            os.environ['GOPATH'] = go_path
            command = []
            command.append(which(args.command))
            command.extend(args.args)
            ret = exec_with_bindmount(args.source, src_path, command, src_path, os.environ)
      except subprocess.CalledProcessError as e:
         sys.stderr.write('Failed bind mount: {0}'.format(e))
         sys.exit(1)
      except Exception as e:
         sys.stderr.write('Failed to execute command: {0}'.format(e))
         sys.exit(1)
      except KeyboardInterrupt:
         sys.exit(2)
      else:
         sys.exit(ret)

      sys.exit(0)

   parser = argparse.ArgumentParser()
   subs = parser.add_subparsers()

   mount_cmd = subs.add_parser('mount')
   mount_cmd.add_argument('-c', '--create-dir', dest='manage_dir', action='store_true', default=False, help='Create the destination directory if it does not exist')
   mount_cmd.add_argument('source', type=abspath, help='Source path to bind mount')
   mount_cmd.add_argument('destination', type=abspath, help='Destination where to bind mount to')
   mount_cmd.set_defaults(func=do_mount)

   umount_cmd = subs.add_parser('umount')
   umount_cmd.add_argument('-r', '--remove-dir', dest='manage_dir', action='store_true', default=False, help='Remove the mountpoint')
   umount_cmd.add_argument('path', type=abspath, help='Bind mounted directory to unmount')
   umount_cmd.set_defaults(func=do_umount)

   exec_cmd = subs.add_parser('exec')
   exec_cmd.add_argument('-m', '--manage-dir', dest='manage_dir', action='store_true', default=False, help='Create/Remove the destination directory')
   exec_cmd.add_argument('-d', '--working-directory', dest='wdir', default=None, help='Change to this directory before executing')
   exec_cmd.add_argument('source', type=abspath, help='Source path to bind mount')
   exec_cmd.add_argument('destination', type=abspath, help='Destination where to bind mount to')
   exec_cmd.add_argument('command', help='The command to execute')
   exec_cmd.add_argument('args', nargs=argparse.REMAINDER, help='Arguments to pass the command')
   exec_cmd.set_defaults(func=do_exec)

   gpm_cmd = subs.add_parser('gpm')
   gpm_cmd.add_argument('source', type=abspath, help='Source path to bind mount')
   gpm_cmd.add_argument('package', type=str, help='Go Package Path')
   gpm_cmd.add_argument('command', help='The command to execute')
   gpm_cmd.add_argument('args', nargs=argparse.REMAINDER, help='Arguments to pass the command')
   gpm_cmd.set_defaults(func=do_gpm)

   args = parser.parse_args()

   args.func(args)
