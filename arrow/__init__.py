# -*- coding: utf-8 -*-
"""箭头消除游戏核心包。

模块划分：
  config      全局常量（窗口/棋盘/颜色/方向/状态机）
  levels      关卡数据
  logic       纯逻辑：Arrow、盘面构建、路径检测
  utils       颜色工具
  ui          字体与箭头绘制
  button      按钮控件
  animations  飞出/碰撞动画
  game        Game 类（状态机、事件、渲染编排）
"""
