# gpm
GOPATH Mapping so you can build outside of the GOPATH

## Requirements

### FUSE + bindfs

MacOS has no builtin bind mounting capabilities so a FUSE + bindfs must be used.

* Fuse for MacOS: https://osxfuse.github.io/
* bindfs: https://bindfs.org/

Linux can also use the bindfs FUSE filesystem. Most likely these packages are available for your distro already and installation should be straight forward.

### `mount`

On Linux the mount command can be used to perform the bind mounting. This however may require root privileges in order to execute `mount`so FUSE should be preferred.

## Usage

### Using the Bash functions and aliases

```
>>> source functions.bash
>>> gpm . github.com/hashicorp/consul make

# You can use aliases too
>>> alias gpm_consul='_gpm_aliasable github.com/hashicorp/consul'
>>> gpm_consul . make
```

### Direct bindutil.py invocation

```
bindutil.py gpm . github.com/hashicorp/consul make
```

## Internals

The `bindutil.py gpm` subcommand will do a few things:

1. Create a temporary directory to store a per-command GOPATH. 
2. Bind mount the desired directory into the per-command GOPATH at `<per-command GOPATH>/src/<package>`
3. Execute the command with the working directory set to the package within the new GOPATH. It also modifies the GOPATH environment variable to add the per-command GOPATH at the front of the list of directories.
4. Unmount the bind mount.
5. Remove the temporary directory and all its contents
