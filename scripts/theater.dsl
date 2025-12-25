# 剧院智能售票机器人脚本
# 场景：查询演出、购票、取票

Step welcome
    Set $ticketCount = 0
    Set $totalPrice = 0
    Set $selectedShow = ""
    Set $selectedSeat = ""
    Speak "欢迎致电星光大剧院！我是智能售票助手小星。请问有什么可以帮您？您可以说：查询演出、购票、取票、会员服务 或 人工客服。"
    Listen 5, 30
    Branch "查询", queryShows
    Branch "演出", queryShows
    Branch "查询演出", queryShows
    Branch "购票", buyTicket
    Branch "买票", buyTicket
    Branch "取票", pickupTicket
    Branch "领票", pickupTicket
    Branch "会员", memberService
    Branch "人工", humanService
    Branch "客服", humanService
    Silence silenceHandler
    Default defaultHandler

Step queryShows
    Speak "好的，为您查询近期演出。【本周热门】1.芭蕾舞剧《天鹅湖》- 周六19:00，票价280-880元；2.话剧《茶馆》- 周日14:00，票价180-580元；3.音乐剧《猫》- 周日19:00，票价380-1280元。请问您对哪场演出感兴趣？"
    Listen 5, 30
    Branch "天鹅湖", showSwanLake
    Branch "芭蕾", showSwanLake
    Branch "茶馆", showTeahouse
    Branch "话剧", showTeahouse
    Branch "猫", showCats
    Branch "音乐剧", showCats
    Branch "更多", moreShows
    Branch "下周", nextWeekShows
    Branch "购票", buyTicket
    Branch "返回", welcome
    Default askShow

Step showSwanLake
    Set $selectedShow = "天鹅湖"
    Set $showTime = "周六19:00"
    Set $showVenue = "大剧场"
    Speak "《天鹅湖》演出信息：经典芭蕾舞剧，由国家芭蕾舞团倾情演绎。演出时间：周六19:00，时长约2小时（含中场休息）。票价：VIP区880元、A区580元、B区380元、C区280元。当前VIP区和A区余票较少。请问您要购买吗？"
    Listen 5, 30
    Branch "购买", selectSeatSwanLake
    Branch "买", selectSeatSwanLake
    Branch "是", selectSeatSwanLake
    Branch "好", selectSeatSwanLake
    Branch "VIP", selectVIP
    Branch "A区", selectAreaA
    Branch "B区", selectAreaB
    Branch "C区", selectAreaC
    Branch "其他", queryShows
    Branch "返回", queryShows
    Default selectSeatSwanLake

Step showTeahouse
    Set $selectedShow = "茶馆"
    Set $showTime = "周日14:00"
    Set $showVenue = "小剧场"
    Speak "《茶馆》演出信息：老舍经典话剧，北京人艺原班人马。演出时间：周日14:00，时长约3小时（含两次中场休息）。票价：VIP区580元、A区380元、B区280元、C区180元。目前各区余票充足。请问您要购买吗？"
    Listen 5, 30
    Branch "购买", selectSeatTeahouse
    Branch "买", selectSeatTeahouse
    Branch "是", selectSeatTeahouse
    Branch "好", selectSeatTeahouse
    Branch "其他", queryShows
    Branch "返回", queryShows
    Default selectSeatTeahouse

Step showCats
    Set $selectedShow = "猫"
    Set $showTime = "周日19:00"
    Set $showVenue = "大剧场"
    Speak "《猫》演出信息：世界经典音乐剧，百老汇原版引进。演出时间：周日19:00，时长约2.5小时（含中场休息）。票价：VIP区1280元、A区880元、B区580元、C区380元。这是本轮演出最后一场，VIP区即将售罄！请问您要购买吗？"
    Listen 5, 30
    Branch "购买", selectSeatCats
    Branch "买", selectSeatCats
    Branch "是", selectSeatCats
    Branch "好", selectSeatCats
    Branch "其他", queryShows
    Branch "返回", queryShows
    Default selectSeatCats

Step moreShows
    Speak "更多演出：4.交响音乐会《贝多芬之夜》- 下周五20:00，票价180-680元；5.儿童剧《小红帽》- 下周六10:00，票价80-280元；6.相声专场《笑傲江湖》- 下周六15:00，票价120-380元。请问您对哪场感兴趣？"
    Listen 5, 30
    Branch "交响", showSymphony
    Branch "贝多芬", showSymphony
    Branch "儿童", showKids
    Branch "小红帽", showKids
    Branch "相声", showCrosstalk
    Branch "返回", queryShows
    Default queryShows

Step nextWeekShows
    Speak "下周演出预告：周五《贝多芬之夜》交响音乐会、周六《小红帽》儿童剧和《笑傲江湖》相声专场、周日《罗密欧与朱丽叶》芭蕾舞剧。需要了解详情吗？"
    Listen 5, 20
    Branch "是", moreShows
    Branch "好", moreShows
    Branch "详情", moreShows
    Branch "返回", queryShows
    Default queryShows

Step showSymphony
    Set $selectedShow = "贝多芬之夜"
    Set $showTime = "下周五20:00"
    Speak "《贝多芬之夜》交响音乐会：演奏贝多芬《命运》《田园》等经典曲目。下周五20:00，票价：A区680元、B区380元、C区180元。请问您要购买吗？"
    Listen 5, 20
    Branch "购买", selectAreaGeneral
    Branch "买", selectAreaGeneral
    Branch "返回", moreShows
    Default selectAreaGeneral

Step showKids
    Set $selectedShow = "小红帽"
    Set $showTime = "下周六10:00"
    Speak "《小红帽》儿童剧：经典童话改编，互动性强，适合3-10岁儿童。下周六10:00，票价：A区280元、B区180元、C区80元。儿童需购票入场。请问您要购买吗？"
    Listen 5, 20
    Branch "购买", selectAreaGeneral
    Branch "买", selectAreaGeneral
    Branch "返回", moreShows
    Default selectAreaGeneral

Step showCrosstalk
    Set $selectedShow = "笑傲江湖"
    Set $showTime = "下周六15:00"
    Speak "《笑傲江湖》相声专场：德云社班底，爆笑全场。下周六15:00，票价：VIP区380元、A区280元、B区180元、C区120元。请问您要购买吗？"
    Listen 5, 20
    Branch "购买", selectAreaGeneral
    Branch "买", selectAreaGeneral
    Branch "返回", moreShows
    Default selectAreaGeneral

Step buyTicket
    Speak "好的，请问您要购买哪场演出的票？您可以说演出名称，或说'查询'查看近期演出。"
    Listen 5, 30
    Branch "天鹅湖", showSwanLake
    Branch "茶馆", showTeahouse
    Branch "猫", showCats
    Branch "查询", queryShows
    Branch "返回", welcome
    Default queryShows

Step selectSeatSwanLake
    Set $selectedShow = "天鹅湖"
    Speak "请选择座位区域：VIP区880元、A区580元、B区380元、C区280元。请问您要哪个区域？"
    Listen 5, 20
    Branch "VIP", selectVIP
    Branch "A区", selectAreaA
    Branch "B区", selectAreaB
    Branch "C区", selectAreaC
    Branch "A", selectAreaA
    Branch "B", selectAreaB
    Branch "C", selectAreaC
    Default selectAreaB

Step selectSeatTeahouse
    Set $selectedShow = "茶馆"
    Speak "请选择座位区域：VIP区580元、A区380元、B区280元、C区180元。请问您要哪个区域？"
    Listen 5, 20
    Branch "VIP", selectVIPTeahouse
    Branch "A区", selectAreaATeahouse
    Branch "B区", selectAreaBTeahouse
    Branch "C区", selectAreaCTeahouse
    Default selectAreaBTeahouse

Step selectSeatCats
    Set $selectedShow = "猫"
    Speak "请选择座位区域：VIP区1280元（仅剩3张）、A区880元、B区580元、C区380元。请问您要哪个区域？"
    Listen 5, 20
    Branch "VIP", selectVIPCats
    Branch "A区", selectAreaACats
    Branch "B区", selectAreaBCats
    Branch "C区", selectAreaCCats
    Default selectAreaBCats

Step selectAreaGeneral
    Speak "请选择座位区域：A区、B区 或 C区？"
    Listen 5, 15
    Branch "A区", selectAreaA
    Branch "A", selectAreaA
    Branch "B区", selectAreaB
    Branch "B", selectAreaB
    Branch "C区", selectAreaC
    Branch "C", selectAreaC
    Default selectAreaB

Step selectVIP
    Set $selectedSeat = "VIP区"
    Set $ticketPrice = 880
    Goto selectQuantity

Step selectAreaA
    Set $selectedSeat = "A区"
    Set $ticketPrice = 580
    Goto selectQuantity

Step selectAreaB
    Set $selectedSeat = "B区"
    Set $ticketPrice = 380
    Goto selectQuantity

Step selectAreaC
    Set $selectedSeat = "C区"
    Set $ticketPrice = 280
    Goto selectQuantity

Step selectVIPTeahouse
    Set $selectedSeat = "VIP区"
    Set $ticketPrice = 580
    Goto selectQuantity

Step selectAreaATeahouse
    Set $selectedSeat = "A区"
    Set $ticketPrice = 380
    Goto selectQuantity

Step selectAreaBTeahouse
    Set $selectedSeat = "B区"
    Set $ticketPrice = 280
    Goto selectQuantity

Step selectAreaCTeahouse
    Set $selectedSeat = "C区"
    Set $ticketPrice = 180
    Goto selectQuantity

Step selectVIPCats
    Set $selectedSeat = "VIP区"
    Set $ticketPrice = 1280
    Goto selectQuantity

Step selectAreaACats
    Set $selectedSeat = "A区"
    Set $ticketPrice = 880
    Goto selectQuantity

Step selectAreaBCats
    Set $selectedSeat = "B区"
    Set $ticketPrice = 580
    Goto selectQuantity

Step selectAreaCCats
    Set $selectedSeat = "C区"
    Set $ticketPrice = 380
    Goto selectQuantity

Step selectQuantity
    Speak "您选择了《" + $selectedShow + "》" + $selectedSeat + "，单价" + $ticketPrice + "元。请问您要购买几张票？"
    Listen 5, 15
    Branch "1", qty1
    Branch "一张", qty1
    Branch "2", qty2
    Branch "两张", qty2
    Branch "3", qty3
    Branch "三张", qty3
    Branch "4", qty4
    Branch "四张", qty4
    Default qty2

Step qty1
    Set $ticketCount = 1
    Goto confirmPurchase

Step qty2
    Set $ticketCount = 2
    Goto confirmPurchase

Step qty3
    Set $ticketCount = 3
    Goto confirmPurchase

Step qty4
    Set $ticketCount = 4
    Goto confirmPurchase

Step confirmPurchase
    Set $totalPrice = $ticketPrice * $ticketCount
    Speak "订单确认：《" + $selectedShow + "》" + $selectedSeat + " " + $ticketCount + "张，总计" + $totalPrice + "元。请问确认购买吗？"
    Listen 5, 20
    Branch "确认", processPayment
    Branch "是", processPayment
    Branch "好", processPayment
    Branch "买", processPayment
    Branch "修改", modifyOrder
    Branch "取消", cancelPurchase
    Default processPayment

Step modifyOrder
    Speak "请问您要修改什么？可以说'换座位'、'换数量'或'换演出'。"
    Listen 5, 15
    Branch "座位", selectSeatSwanLake
    Branch "数量", selectQuantity
    Branch "演出", queryShows
    Branch "返回", confirmPurchase
    Default confirmPurchase

Step cancelPurchase
    Speak "订单已取消。请问还需要其他帮助吗？"
    Listen 5, 15
    Branch "是", welcome
    Branch "查询", queryShows
    Branch "没有", goodbye
    Default welcome

Step processPayment
    Speak "正在为您生成订单...订单号：T20241225001。总金额" + $totalPrice + "元。请选择支付方式：微信、支付宝 或 银行卡。"
    Listen 5, 20
    Branch "微信", payWeChat
    Branch "支付宝", payAlipay
    Branch "银行卡", payCard
    Branch "刷卡", payCard
    Default payWeChat

Step payWeChat
    Speak "请使用微信扫描二维码支付" + $totalPrice + "元...支付成功！"
    Goto paymentSuccess

Step payAlipay
    Speak "请使用支付宝扫描二维码支付" + $totalPrice + "元...支付成功！"
    Goto paymentSuccess

Step payCard
    Speak "请输入银行卡信息支付" + $totalPrice + "元...支付成功！"
    Goto paymentSuccess

Step paymentSuccess
    Set $ticketCode = "886425"
    Speak "恭喜您购票成功！您的取票码是：" + $ticketCode + "。请于演出当天提前30分钟到剧院自助取票机或人工窗口凭取票码取票。电子票也已发送至您的手机。还需要其他帮助吗？"
    Listen 5, 20
    Branch "是", welcome
    Branch "取票", pickupInfo
    Branch "没有", goodbye
    Branch "谢谢", goodbye
    Default goodbye

Step pickupTicket
    Speak "好的，为您办理取票服务。请问您是通过取票码取票还是身份证取票？"
    Listen 5, 20
    Branch "取票码", pickupByCode
    Branch "身份证", pickupByID
    Branch "电子票", eTicketInfo
    Default pickupByCode

Step pickupByCode
    Speak "请输入您的6位取票码。"
    Listen 5, 30
    Default verifyCode

Step verifyCode
    Set $inputCode = "886425"
    Speak "取票码验证成功！您的票务信息：《" + $selectedShow + "》，" + $selectedSeat + " " + $ticketCount + "张。您可以在以下方式取票：1.剧院大厅自助取票机 2.人工售票窗口。建议演出前30分钟到场取票。"
    Goto pickupInfo

Step pickupByID
    Speak "请持购票时使用的身份证原件到剧院人工窗口取票。窗口服务时间：每日9:00-20:00。"
    Goto pickupInfo

Step eTicketInfo
    Speak "您的电子票已发送至购票手机号码，也可在星光剧院APP或微信小程序中查看。入场时请出示电子票二维码。"
    Goto pickupInfo

Step pickupInfo
    Speak "取票地点：星光大剧院一层大厅。自助取票机开放时间：演出前2小时至开演。人工窗口：每日9:00-20:00。演出前30分钟停止取票入场。还有其他问题吗？"
    Listen 5, 20
    Branch "是", welcome
    Branch "停车", parkingInfo
    Branch "交通", trafficInfo
    Branch "没有", goodbye
    Default goodbye

Step parkingInfo
    Speak "剧院设有地下停车场，可提供200个车位。演出期间前2小时免费停车，之后每小时10元。建议提前到达或选择公共交通。"
    Goto pickupInfo

Step trafficInfo
    Speak "交通指南：地铁1号线星光站A出口步行5分钟；公交101、102、103路星光剧院站；自驾可导航至星光大剧院。"
    Goto pickupInfo

Step memberService
    Speak "会员服务：普通会员享9.5折优惠；黄金会员享9折优惠及优先选座；钻石会员享8.5折优惠、专属休息室及免费停车。请问您要办理会员卡还是查询会员权益？"
    Listen 5, 20
    Branch "办理", registerMember
    Branch "查询", queryMember
    Branch "权益", memberBenefits
    Branch "返回", welcome
    Default memberBenefits

Step registerMember
    Speak "办理会员卡：普通会员免费注册；黄金会员年费299元；钻石会员年费999元。请到剧院服务台办理或在APP中注册。还需要其他帮助吗？"
    Listen 5, 15
    Branch "是", welcome
    Branch "没有", goodbye
    Default goodbye

Step queryMember
    Speak "请输入您的会员卡号或手机号查询会员信息。"
    Listen 5, 20
    Default memberInfo

Step memberInfo
    Speak "查询到您的会员信息：黄金会员，积分3500分，可兑换价值350元的优惠券。本月您有2张会员专属折扣券可用。还需要其他帮助吗？"
    Listen 5, 15
    Branch "是", welcome
    Branch "兑换", redeemPoints
    Branch "没有", goodbye
    Default goodbye

Step redeemPoints
    Speak "积分兑换：1000积分=100元优惠券，可在购票时抵扣使用。您当前有3500积分，可兑换300元优惠券。是否兑换？"
    Listen 5, 15
    Branch "是", confirmRedeem
    Branch "兑换", confirmRedeem
    Branch "不", welcome
    Default welcome

Step confirmRedeem
    Speak "兑换成功！300元优惠券已发放至您的账户，有效期30天。可在购票时使用。还需要其他帮助吗？"
    Listen 5, 15
    Branch "是", welcome
    Branch "购票", queryShows
    Branch "没有", goodbye
    Default goodbye

Step memberBenefits
    Speak "会员权益说明：【普通会员】购票9.5折、积分累积；【黄金会员】购票9折、优先选座、生日礼券、积分双倍；【钻石会员】购票8.5折、专属休息室、免费停车、演出节目单、积分三倍。还需要其他帮助吗？"
    Listen 5, 15
    Branch "办理", registerMember
    Branch "是", welcome
    Branch "没有", goodbye
    Default goodbye

Step humanService
    Speak "正在为您转接人工客服，请稍候...人工客服服务时间：每日9:00-21:00。您也可以拨打服务热线400-123-4567。"
    Exit

Step askShow
    Speak "抱歉，没有听清您要查询的演出。请说出演出名称，例如：天鹅湖、茶馆、猫等。或说'查询'查看所有演出。"
    Listen 5, 20
    Branch "天鹅湖", showSwanLake
    Branch "茶馆", showTeahouse
    Branch "猫", showCats
    Branch "查询", queryShows
    Default queryShows

Step silenceHandler
    Speak "您好，请问还在吗？如需购票请说演出名称，如需取票请说'取票'，需要其他帮助请说'帮助'。"
    Listen 5, 20
    Branch "购票", queryShows
    Branch "取票", pickupTicket
    Branch "帮助", welcome
    Silence goodbye
    Default welcome

Step defaultHandler
    Speak "抱歉，我没有理解您的意思。您可以说：查询演出、购票、取票、会员服务 或 人工客服。请问需要什么帮助？"
    Listen 5, 20
    Branch "查询", queryShows
    Branch "购票", buyTicket
    Branch "取票", pickupTicket
    Branch "会员", memberService
    Branch "人工", humanService
    Default welcome

Step goodbye
    Speak "感谢您使用星光大剧院智能售票服务，期待您的光临！再见！"
    Exit
