# gpm
GOPATH Mapping so you can build outside of the GOPATH

## Usage (from bash)

```
>>> source functions.bash
>>> gpm . github.com/hashicorp/consul make

# You can use aliases too
>>> alias gpm_consul='_gpm_aliasable github.com/hashicorp/consul'
>>> gpm_consul . make
```