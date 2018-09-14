pushd $(dirname ${BASH_SOURCE[0]}) > /dev/null
ENV_DIR=$(pwd)
popd > /dev/null

alias bindutil='python ${ENV_DIR}/bindutil.py'

function bindutil {
   python ${ENV_DIR}/bindutil.py $@
}

function bindmount {
   bindutil mount $1 $2
}

function unbindmount {
   bindutil umount $1
}

function bind_exec {
   bindutil exec $@
}

function gpm_mount {
   bindutil mount $1 ${GOPATH}/src/${2}
}

function gpm_umount {
   bindutil umount ${GOPATH}/src/${2}
}

function gpm {
   src=$1
   dest=$2
   mkdir -p ${GOPATH}/src/${dest}
   shift 2
   bindutil exec $src ${GOPATH}/src/${dest} "$@"
}

function _gpm_aliasable {
   package=$1
   mdir=$2
   shift 2
   gpm $mdir $package -d "${GOPATH}/src/${package}" "$@"
}
