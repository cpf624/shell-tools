#!/bin/bash
# Author:   jhat
# Email:    cpf624@126.com
# Date:     2013-10-30
# Describe: Web文件热部署

# 项目名
project_name='xauth-test'
# 项目版本
project_version='1.0'
# 运行端口
run_port='8081'
# 监听路径
# listen_path='src/main/webapp'
listen_path='../xauth-web/src/main/resources/META-INF/resources'
# 热部署路径
# dest_path="target/$project_name-$project_version"
dest_path="src/main/webapp"
# 端口检查开始时间(s)
check_start=30
# 端口检查间隔时间(s)
check_slice=5

# 去除热部署路径最后一个 /
path_len=${#dest_path}
let 'path_len--'
if [ ${dest_path:$path_len:1} == '/' ]; then
    dest_path=${dest_path:0:$path_len}
fi

# 监听路径长度
path_len=${#listen_path}

# 检查系统是否已安装 inotify-tools
type inotifywait > /dev/null 2>&1
if [ $? -ne 0 ]; then
    sudo apt-get install inotify-tools
fi

# 端口检查,如果端口不再占用则杀死目录监听进程
cat << EOF > /tmp/hotdeploy_check.sh
sleep $check_start
while [ 1 ];
do
    if [ \$(netstat -an | grep ":$run_port" | \
        awk '\$NF == "LISTEN" \
        {print \$0}' | wc -l) -eq 0 ]; then
        break
    fi
    sleep $check_slice
done
pkill -P $$
EOF
chmod u+x '/tmp/hotdeploy_check.sh'
/tmp/hotdeploy_check.sh > /dev/null 2>&1 &
rm /tmp/hotdeploy_check.sh

# 文件权限 rwx 转数字
function octal_access(){
    access=$1
    octal=0
    if [ ! ${access:0:1} == '-' ]; then
        let 'octal += 4'
    fi
    if [ ! ${access:1:1} == '-' ]; then
        let 'octal += 2'
    fi
    if [ ! ${access:2:1} == '-' ]; then
        let 'octal += 1'
    fi
    echo $octal
}

# 保证目标父目录存在
function fix_parent() {
    file="$1"
    parent="${file%/*}"
    if [ ! -e "$parent" ]; then
        mkdir -p "$parent" > /dev/null 2>&1
    fi
}

# 监听目录变化并进行热部署
inotifywait -mrq "${listen_path}" --format '%e %w %f' \
-e 'create,modify,moved_to,moved_from,delete,attrib' \
| while read event wfile efile
do
    action=${event%%,*}
    src_file="${wfile}${efile}"
    dst_file="$dest_path${src_file:$path_len}"

    case $action in
    CREATE | MODIFY | MOVED_TO)
        $(fix_parent "$dst_file")
        cp -r "$src_file" "$dst_file" > /dev/null 2>&1
    ;;
    DELETE | MOVED_FROM)
        rm -rf "$dst_file" > /dev/null 2>&1
    ;;
    ATTRIB)
        if [ ! -e "$src_file" ]; then
            continue
        fi
        attr=$(ls -ld "$src_file")
        u=$(octal_access ${attr:1:3})
        g=$(octal_access ${attr:4:3})
        o=$(octal_access ${attr:7:3})
        $(fix_parent "$dst_file")
        if [ ! -e "$dst_file" ]; then
            cp -r "$src_file" "$dst_file" > /dev/null 2>&1
        else
            chmod $u$g$o "$dst_file" > /dev/null 2>&1
        fi
    ;;
    esac
done
