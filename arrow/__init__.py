# -*- coding: utf-8 -*-
"""箭头消除游戏核心包。

职责分层：
  config/    全局配置包（layout 布局 / palette 颜色 / rules 规则）
  levels/    关卡数据包（每关一个模块，__init__ 聚合为 LEVELS）
  core/      纯逻辑层（Arrow、盘面规则、颜色工具，不依赖 pygame）
  view/      表现层（字体、箭头绘制、按钮、动画，依赖 pygame）
  game.py    Game 类（状态机、事件、渲染编排）
"""
