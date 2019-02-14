# gpm
GOPATH Mapping so you can build outside of the GOPATH

## Requirements

### FUSE + bindfs

MacOS has no builtin bind mounting capabilities so a FUSE + bindfs must be used based filesystem must be used.

* Fuse for MacOS: https://osxfuse.github.io/
* bindfs: https://bindfs.org/

Linux can also use the bindfs FUSE filesystem. Most likely these packages are available for your distro already and installation should be straight forward.

### `mount`

On Linux the mount command can be used to perform the bind mounting. This however may require root privileges in order to execute `mount`

## Usage (from bash)

```
>>> source functions.bash
>>> gpm . github.com/hashicorp/consul make

# You can use aliases too
>>> alias gpm_consul='_gpm_aliasable github.com/hashicorp/consul'
>>> gpm_consul . make
```
