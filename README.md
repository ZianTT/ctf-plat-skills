# CTF Platform Workflow Skill

CTF AI 自动化的最后一座桥梁，打通CTF平台与AI的通信壁垒

## 目前支持及计划支持平台

- [x] ZEROSECONE（即阿里云CTF等所用平台，可能非官方命名）
- [x] GZCTF
- [ ] Ret2Shell
- [ ] CTFd
- [ ] 新版 adworld 攻防世界（XCTF、赛宁网安）
- [ ] i春秋
- [ ] CTFPlus
- [ ] A1CTF


## 已知问题

在 TCP over WebSocket 模式 (WSRX)模式下，模型可能不会很好的连接题目，需进行改进。

模型无法自动做到容器延期

模型无法自动下载复杂的外部附件情况