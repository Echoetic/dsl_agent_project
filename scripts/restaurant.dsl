# 餐厅智能点餐机器人脚本
# 场景：点餐、查看菜单、付账

Step welcome
    Set $totalAmount = 0
    Set $orderItems = ""
    Set $itemCount = 0
    Speak "欢迎光临美味餐厅！我是您的智能点餐助手小美。请问您需要什么服务？您可以说：点餐、查看菜单、推荐菜品 或 呼叫服务员。"
    Listen 5, 30
    Branch "点餐", startOrder
    Branch "菜单", showMenu
    Branch "查看菜单", showMenu
    Branch "推荐", recommend
    Branch "推荐菜品", recommend
    Branch "服务员", callWaiter
    Branch "呼叫服务员", callWaiter
    Branch "结账", checkout
    Branch "付账", checkout
    Silence silenceHandler
    Default defaultHandler

Step showMenu
    Speak "好的，这是我们的菜单。【热菜】红烧肉48元、清蒸鱼68元、宫保鸡丁38元、麻婆豆腐28元、糖醋排骨58元。【凉菜】凉拌黄瓜18元、口水鸡32元。【主食】米饭3元、炒面18元、馒头2元。【饮品】可乐5元、橙汁8元、啤酒15元。请问您要点什么？"
    Listen 5, 45
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "麻婆豆腐", orderMapodoufu
    Branch "糖醋排骨", orderTangcupaigu
    Branch "凉拌黄瓜", orderHuanggua
    Branch "口水鸡", orderKoushuiji
    Branch "米饭", orderRice
    Branch "炒面", orderNoodles
    Branch "可乐", orderCola
    Branch "橙汁", orderOrangeJuice
    Branch "啤酒", orderBeer
    Branch "推荐", recommend
    Branch "点餐", startOrder
    Branch "结账", checkout
    Branch "返回", welcome
    Default askDish

Step recommend
    Speak "今日推荐：招牌红烧肉（选用上等五花肉，肥而不腻）48元；清蒸鲈鱼（当日新鲜捕捞）68元；宫保鸡丁（川味经典，麻辣鲜香）38元。套餐推荐：商务套餐（红烧肉+米饭+时蔬+饮品）58元。请问您要点哪个？"
    Listen 5, 30
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "鲈鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "套餐", orderCombo
    Branch "商务套餐", orderCombo
    Branch "菜单", showMenu
    Branch "返回", welcome
    Default startOrder

Step startOrder
    Speak "好的，开始为您点餐。请告诉我您想要的菜品，例如：'来一份红烧肉'或'两份米饭'。说'完成'结束点餐，说'菜单'查看菜单。"
    Listen 5, 45
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "麻婆豆腐", orderMapodoufu
    Branch "糖醋排骨", orderTangcupaigu
    Branch "凉拌黄瓜", orderHuanggua
    Branch "口水鸡", orderKoushuiji
    Branch "米饭", orderRice
    Branch "炒面", orderNoodles
    Branch "馒头", orderMantou
    Branch "可乐", orderCola
    Branch "橙汁", orderOrangeJuice
    Branch "啤酒", orderBeer
    Branch "套餐", orderCombo
    Branch "完成", confirmOrder
    Branch "结账", confirmOrder
    Branch "菜单", showMenu
    Branch "取消", cancelOrder
    Default askDish

Step orderHongshaoru
    Set $totalAmount = $totalAmount + 48
    Set $itemCount = $itemCount + 1
    Set $lastItem = "红烧肉"
    Speak "好的，为您添加红烧肉1份（48元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？说'完成'结束点餐。"
    Listen 5, 30
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "麻婆豆腐", orderMapodoufu
    Branch "米饭", orderRice
    Branch "可乐", orderCola
    Branch "完成", confirmOrder
    Branch "结账", confirmOrder
    Branch "取消", cancelLastItem
    Branch "菜单", showMenu
    Default continueOrder

Step orderQingzhengyu
    Set $totalAmount = $totalAmount + 68
    Set $itemCount = $itemCount + 1
    Set $lastItem = "清蒸鱼"
    Speak "好的，为您添加清蒸鱼1份（68元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "米饭", orderRice
    Branch "可乐", orderCola
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderGongbaojiding
    Set $totalAmount = $totalAmount + 38
    Set $itemCount = $itemCount + 1
    Set $lastItem = "宫保鸡丁"
    Speak "好的，为您添加宫保鸡丁1份（38元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "米饭", orderRice
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderMapodoufu
    Set $totalAmount = $totalAmount + 28
    Set $itemCount = $itemCount + 1
    Set $lastItem = "麻婆豆腐"
    Speak "好的，为您添加麻婆豆腐1份（28元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "米饭", orderRice
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderTangcupaigu
    Set $totalAmount = $totalAmount + 58
    Set $itemCount = $itemCount + 1
    Set $lastItem = "糖醋排骨"
    Speak "好的，为您添加糖醋排骨1份（58元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderHuanggua
    Set $totalAmount = $totalAmount + 18
    Set $itemCount = $itemCount + 1
    Set $lastItem = "凉拌黄瓜"
    Speak "好的，为您添加凉拌黄瓜1份（18元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderKoushuiji
    Set $totalAmount = $totalAmount + 32
    Set $itemCount = $itemCount + 1
    Set $lastItem = "口水鸡"
    Speak "好的，为您添加口水鸡1份（32元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderRice
    Set $totalAmount = $totalAmount + 3
    Set $itemCount = $itemCount + 1
    Set $lastItem = "米饭"
    Speak "好的，为您添加米饭1份（3元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Branch "米饭", orderRice
    Default continueOrder

Step orderNoodles
    Set $totalAmount = $totalAmount + 18
    Set $itemCount = $itemCount + 1
    Set $lastItem = "炒面"
    Speak "好的，为您添加炒面1份（18元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderMantou
    Set $totalAmount = $totalAmount + 2
    Set $itemCount = $itemCount + 1
    Set $lastItem = "馒头"
    Speak "好的，为您添加馒头1个（2元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderCola
    Set $totalAmount = $totalAmount + 5
    Set $itemCount = $itemCount + 1
    Set $lastItem = "可乐"
    Speak "好的，为您添加可乐1瓶（5元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderOrangeJuice
    Set $totalAmount = $totalAmount + 8
    Set $itemCount = $itemCount + 1
    Set $lastItem = "橙汁"
    Speak "好的，为您添加橙汁1杯（8元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderBeer
    Set $totalAmount = $totalAmount + 15
    Set $itemCount = $itemCount + 1
    Set $lastItem = "啤酒"
    Speak "好的，为您添加啤酒1瓶（15元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step orderCombo
    Set $totalAmount = $totalAmount + 58
    Set $itemCount = $itemCount + 1
    Set $lastItem = "商务套餐"
    Speak "好的，为您添加商务套餐1份（红烧肉+米饭+时蔬+饮品，58元）。当前已点" + $itemCount + "个菜品，小计" + $totalAmount + "元。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "取消", cancelLastItem
    Default continueOrder

Step continueOrder
    Speak "好的，请继续点餐。您可以说菜品名称，或说'完成'结束点餐，'菜单'查看菜单。"
    Listen 5, 30
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "麻婆豆腐", orderMapodoufu
    Branch "米饭", orderRice
    Branch "可乐", orderCola
    Branch "完成", confirmOrder
    Branch "菜单", showMenu
    Default askDish

Step cancelLastItem
    Speak "好的，已取消最后一个菜品。还需要点什么？"
    Listen 5, 30
    Branch "完成", confirmOrder
    Branch "继续", continueOrder
    Default continueOrder

Step cancelOrder
    Speak "您确定要取消整个订单吗？说'确定'取消订单，说'继续'继续点餐。"
    Listen 5, 15
    Branch "确定", orderCancelled
    Branch "是", orderCancelled
    Branch "继续", continueOrder
    Branch "不", continueOrder
    Default continueOrder

Step orderCancelled
    Set $totalAmount = 0
    Set $itemCount = 0
    Speak "订单已取消。期待下次为您服务！"
    Exit

Step confirmOrder
    Speak "好的，您的订单确认：共" + $itemCount + "个菜品，总计" + $totalAmount + "元。请问确认下单吗？"
    Listen 5, 20
    Branch "确认", submitOrder
    Branch "是", submitOrder
    Branch "好", submitOrder
    Branch "下单", submitOrder
    Branch "修改", modifyOrder
    Branch "取消", cancelOrder
    Branch "加菜", continueOrder
    Default submitOrder

Step emptyOrder
    Speak "您还没有点任何菜品哦。请先点餐再结账。"
    Goto startOrder

Step submitOrder
    Set $orderNo = "D20241225001"
    Speak "订单提交成功！订单号：" + $orderNo + "，总计" + $totalAmount + "元。菜品正在准备中，预计15分钟后上菜。请问现在结账还是用餐后结账？"
    Listen 5, 20
    Branch "现在", checkout
    Branch "结账", checkout
    Branch "用餐后", waitPayment
    Branch "稍后", waitPayment
    Default waitPayment

Step modifyOrder
    Speak "请问您要修改什么？您可以说'取消最后一个'、'加菜'或'重新点餐'。"
    Listen 5, 20
    Branch "取消", cancelLastItem
    Branch "加菜", continueOrder
    Branch "重新", newOrder
    Default continueOrder

Step newOrder
    Set $totalAmount = 0
    Set $itemCount = 0
    Speak "好的，已清空订单。请重新点餐。"
    Goto startOrder

Step checkout
    Speak "好的，您的订单总计" + $totalAmount + "元。请选择支付方式：微信、支付宝、现金 或 刷卡。"
    Listen 5, 20
    Branch "微信", payWeChat
    Branch "支付宝", payAlipay
    Branch "现金", payCash
    Branch "刷卡", payCard
    Default payWeChat

Step payWeChat
    Set $payMethod = "微信支付"
    Speak "请打开微信扫描二维码完成支付，金额" + $totalAmount + "元...支付成功！感谢您的惠顾！"
    Goto paymentSuccess

Step payAlipay
    Set $payMethod = "支付宝"
    Speak "请打开支付宝扫描二维码完成支付，金额" + $totalAmount + "元...支付成功！感谢您的惠顾！"
    Goto paymentSuccess

Step payCash
    Set $payMethod = "现金"
    Speak "好的，您需要支付现金" + $totalAmount + "元。请将现金交给服务员。支付成功！感谢您的惠顾！"
    Goto paymentSuccess

Step payCard
    Set $payMethod = "银行卡"
    Speak "请插入或刷银行卡，金额" + $totalAmount + "元...支付成功！感谢您的惠顾！"
    Goto paymentSuccess

Step paymentSuccess
    Speak "支付完成！感谢您使用" + $payMethod + "支付" + $totalAmount + "元。欢迎下次光临美味餐厅！祝您用餐愉快！"
    Exit

Step waitPayment
    Speak "好的，用餐结束后可以说'结账'或呼叫服务员结账。祝您用餐愉快！"
    Listen 5, 60
    Branch "结账", checkout
    Branch "加菜", continueOrder
    Branch "服务员", callWaiter
    Branch "谢谢", goodbye
    Default waitPayment

Step callWaiter
    Speak "好的，正在为您呼叫服务员，请稍候..."
    Exit

Step askDish
    Speak "抱歉，我没有听清您要点什么。请说出菜品名称，例如：红烧肉、清蒸鱼、宫保鸡丁等。或说'菜单'查看完整菜单。"
    Listen 5, 30
    Branch "菜单", showMenu
    Branch "红烧肉", orderHongshaoru
    Branch "清蒸鱼", orderQingzhengyu
    Branch "宫保鸡丁", orderGongbaojiding
    Branch "完成", confirmOrder
    Default continueOrder

Step silenceHandler
    Speak "您好，请问还在吗？如需点餐请说出菜品名称，说'菜单'查看菜单，说'结账'进行结账。"
    Listen 5, 20
    Branch "菜单", showMenu
    Branch "点餐", startOrder
    Branch "结账", checkout
    Silence goodbye
    Default welcome

Step defaultHandler
    Speak "抱歉，我没有理解您的意思。您可以说：点餐、查看菜单、推荐菜品、结账 或 呼叫服务员。"
    Listen 5, 20
    Branch "点餐", startOrder
    Branch "菜单", showMenu
    Branch "推荐", recommend
    Branch "结账", checkout
    Branch "服务员", callWaiter
    Default welcome

Step goodbye
    Speak "感谢您光临美味餐厅，期待下次为您服务！再见！"
    Exit
