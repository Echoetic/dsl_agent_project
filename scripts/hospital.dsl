# 医院智能客服机器人脚本
# 场景：看病挂号、缴费、取药

Step welcome
    Speak "您好，欢迎致电XX医院智能客服系统。请问有什么可以帮您？您可以说：挂号、缴费、取药、查询 或 人工服务。"
    Listen 5, 30
    Branch "挂号", registration
    Branch "缴费", payment
    Branch "取药", pharmacy
    Branch "查询", query
    Branch "人工服务", humanService
    Branch "人工", humanService
    Silence silenceHandler
    Default defaultHandler

Step registration
    Speak "好的，为您办理挂号服务。请问您要挂哪个科室？我们有：内科、外科、儿科、妇产科、眼科、口腔科。"
    Listen 5, 30
    Branch "内科", regInternal
    Branch "外科", regSurgery
    Branch "儿科", regPediatrics
    Branch "妇产科", regObstetrics
    Branch "眼科", regOphthalmology
    Branch "口腔科", regDental
    Branch "返回", welcome
    Default askDepartment

Step regInternal
    Set $department = "内科"
    Speak "您选择了内科。内科目前有张医生（主任医师）和李医生（副主任医师）可以预约。请问您要预约哪位医生？"
    Listen 5, 30
    Branch "张医生", confirmRegZhang
    Branch "李医生", confirmRegLi
    Branch "都可以", confirmRegAny
    Branch "返回", registration
    Default askDoctor

Step regSurgery
    Set $department = "外科"
    Speak "您选择了外科。外科目前有王医生（主任医师）和赵医生（副主任医师）可以预约。请问您要预约哪位医生？"
    Listen 5, 30
    Branch "王医生", confirmRegWang
    Branch "赵医生", confirmRegZhao
    Branch "都可以", confirmRegAny
    Branch "返回", registration
    Default askDoctor

Step regPediatrics
    Set $department = "儿科"
    Goto confirmRegAny

Step regObstetrics
    Set $department = "妇产科"
    Goto confirmRegAny

Step regOphthalmology
    Set $department = "眼科"
    Goto confirmRegAny

Step regDental
    Set $department = "口腔科"
    Goto confirmRegAny

Step confirmRegZhang
    Set $doctor = "张医生"
    Goto createRegistration

Step confirmRegLi
    Set $doctor = "李医生"
    Goto createRegistration

Step confirmRegWang
    Set $doctor = "王医生"
    Goto createRegistration

Step confirmRegZhao
    Set $doctor = "赵医生"
    Goto createRegistration

Step confirmRegAny
    Set $doctor = "系统分配"
    Goto createRegistration

Step createRegistration
    Call 创建挂号($department, $doctor) = $registration
    Set $orderNo = "H2024001"
    Speak "挂号成功！您的挂号信息如下：科室：" + $department + "，医生：" + $doctor + "。挂号费为50元，请问是否现在缴费？"
    Listen 5, 20
    Branch "是", payRegistration
    Branch "好", payRegistration
    Branch "缴费", payRegistration
    Branch "现在缴", payRegistration
    Branch "否", registrationComplete
    Branch "稍后", registrationComplete
    Branch "不用", registrationComplete
    Default payRegistration

Step payRegistration
    Set $amount = 50
    Speak "正在为您处理挂号费缴费，金额50元。请确认支付？"
    Listen 5, 15
    Branch "确认", processPayment
    Branch "是", processPayment
    Branch "好", processPayment
    Branch "取消", welcome
    Default processPayment

Step processPayment
    Call 处理缴费($orderNo, $amount) = $payResult
    Speak "缴费成功！交易金额：" + $amount + "元。请您在预约时间前往" + $department + "就诊。还有其他需要帮助的吗？"
    Listen 5, 20
    Branch "有", welcome
    Branch "没有", goodbye
    Branch "没了", goodbye
    Branch "再见", goodbye
    Default goodbye

Step registrationComplete
    Speak "好的，您可以稍后在医院自助机或收费窗口完成缴费。您的挂号单号是" + $orderNo + "。还有其他需要帮助的吗？"
    Listen 5, 20
    Branch "有", welcome
    Branch "没有", goodbye
    Branch "再见", goodbye
    Default goodbye

Step payment
    Speak "好的，为您办理缴费服务。请问您的就诊卡号或挂号单号是多少？"
    Listen 5, 30
    Branch "查询", queryPayment
    Default inputOrderNo

Step inputOrderNo
    Set $orderNo = "待输入"
    Speak "请稍等，正在查询您的待缴费项目..."
    Call 查询费用($orderNo) = $feeInfo
    Set $totalFee = 400
    Speak "查询到您有以下待缴费项目：挂号费50元、检查费200元、药费150元，共计400元。请问是否确认缴费？"
    Listen 5, 20
    Branch "确认", confirmPayAll
    Branch "是", confirmPayAll
    Branch "好", confirmPayAll
    Branch "取消", welcome
    Branch "分开", payOptions
    Default confirmPayAll

Step confirmPayAll
    Set $amount = 400
    Call 处理缴费($orderNo, $amount) = $payResult
    Speak "缴费成功！共缴费400元。您可以前往相应科室就诊或到药房取药。还有其他需要帮助的吗？"
    Listen 5, 20
    Branch "有", welcome
    Branch "取药", pharmacy
    Branch "没有", goodbye
    Default goodbye

Step payOptions
    Speak "好的，请问您要缴纳哪一项？1.挂号费50元 2.检查费200元 3.药费150元"
    Listen 5, 20
    Branch "挂号费", payRegFee
    Branch "检查费", payCheckFee
    Branch "药费", payMedFee
    Branch "全部", confirmPayAll
    Default confirmPayAll

Step payRegFee
    Set $amount = 50
    Speak "正在为您缴纳挂号费50元..."
    Call 处理缴费($orderNo, $amount) = $payResult
    Speak "挂号费缴纳成功！还需要缴纳其他费用吗？"
    Listen 5, 15
    Branch "是", payOptions
    Branch "有", payOptions
    Branch "没有", goodbye
    Default goodbye

Step payCheckFee
    Set $amount = 200
    Speak "正在为您缴纳检查费200元..."
    Call 处理缴费($orderNo, $amount) = $payResult
    Speak "检查费缴纳成功！还需要缴纳其他费用吗？"
    Listen 5, 15
    Branch "是", payOptions
    Branch "有", payOptions
    Branch "没有", goodbye
    Default goodbye

Step payMedFee
    Set $amount = 150
    Speak "正在为您缴纳药费150元..."
    Call 处理缴费($orderNo, $amount) = $payResult
    Speak "药费缴纳成功！您现在可以去药房取药了。还有其他需要帮助的吗？"
    Listen 5, 15
    Branch "是", welcome
    Branch "取药", pharmacy
    Branch "没有", goodbye
    Default goodbye

Step queryPayment
    Speak "请输入您的就诊卡号进行查询..."
    Listen 5, 30
    Default inputOrderNo

Step pharmacy
    Speak "好的，为您查询取药信息。请问您的取药单号或就诊卡号是多少？"
    Listen 5, 30
    Default checkPharmacy

Step checkPharmacy
    Call 获取取药信息($orderNo) = $pharmacyInfo
    Speak "查询到您的取药信息：请到3号窗口取药，目前前面还有5位患者等候。请携带好您的缴费凭证。还有其他需要帮助的吗？"
    Listen 5, 20
    Branch "有", welcome
    Branch "没有", goodbye
    Branch "再见", goodbye
    Default goodbye

Step query
    Speak "请问您要查询什么信息？可以说：挂号记录、缴费记录、检查报告 或 出诊时间。"
    Listen 5, 20
    Branch "挂号记录", queryRegistration
    Branch "缴费记录", queryPaymentRecord
    Branch "检查报告", queryReport
    Branch "出诊时间", querySchedule
    Branch "返回", welcome
    Default queryHelp

Step queryRegistration
    Speak "您近期的挂号记录：12月20日内科张医生（已就诊），12月25日外科王医生（待就诊）。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "没有", goodbye
    Default goodbye

Step queryPaymentRecord
    Speak "您近期的缴费记录：12月20日缴费350元（挂号费+检查费），12月22日缴费180元（药费）。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "没有", goodbye
    Default goodbye

Step queryReport
    Speak "您有一份检查报告已出：血常规检查报告（12月20日）。您可以在医院公众号查看详情或到门诊自助机打印。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "没有", goodbye
    Default goodbye

Step querySchedule
    Speak "请问您要查询哪个科室的出诊时间？"
    Listen 5, 20
    Branch "内科", scheduleInternal
    Branch "外科", scheduleSurgery
    Default scheduleAll

Step scheduleInternal
    Speak "内科出诊时间：周一至周五 8:00-17:00，周六 8:00-12:00。张医生：周一、三、五全天；李医生：周二、四全天。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "挂号", registration
    Branch "没有", goodbye
    Default goodbye

Step scheduleSurgery
    Speak "外科出诊时间：周一至周五 8:00-17:00。王医生：周一、三上午；赵医生：周二、四、五全天。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "挂号", registration
    Branch "没有", goodbye
    Default goodbye

Step scheduleAll
    Speak "各科室出诊时间：周一至周五 8:00-17:00，周六上午8:00-12:00部分科室开诊。详细信息可在医院官网查询。还需要其他帮助吗？"
    Listen 5, 15
    Branch "有", welcome
    Branch "没有", goodbye
    Default goodbye

Step queryHelp
    Speak "抱歉，没有找到相关信息。您可以说：挂号记录、缴费记录、检查报告或出诊时间进行查询。"
    Listen 5, 20
    Branch "挂号记录", queryRegistration
    Branch "缴费记录", queryPaymentRecord
    Branch "检查报告", queryReport
    Branch "出诊时间", querySchedule
    Branch "返回", welcome
    Default welcome

Step humanService
    Speak "好的，正在为您转接人工服务，请稍候...人工服务时间为周一至周五8:00-20:00，周末9:00-17:00。如需继续使用智能服务，请说'返回'。"
    Listen 5, 30
    Branch "返回", welcome
    Default humanWaiting

Step humanWaiting
    Speak "人工客服正忙，您是第3位等候者，预计等待时间2分钟。是否继续等待？"
    Listen 5, 15
    Branch "是", humanConnecting
    Branch "等", humanConnecting
    Branch "不等", welcome
    Branch "返回", welcome
    Default humanConnecting

Step humanConnecting
    Speak "正在连接人工客服，请稍候..."
    Exit

Step askDepartment
    Speak "抱歉，没有听清您要挂哪个科室。请重新说一下，我们有：内科、外科、儿科、妇产科、眼科、口腔科。"
    Listen 5, 30
    Branch "内科", regInternal
    Branch "外科", regSurgery
    Branch "儿科", regPediatrics
    Branch "妇产科", regObstetrics
    Branch "眼科", regOphthalmology
    Branch "口腔科", regDental
    Branch "返回", welcome
    Default welcome

Step askDoctor
    Speak "抱歉，没有听清您选择的医生。请重新说一下医生姓名，或说'都可以'由系统为您分配。"
    Listen 5, 20
    Branch "都可以", confirmRegAny
    Branch "返回", registration
    Default registration

Step silenceHandler
    Speak "您好，请问还在吗？如需帮助请说出您的需求，如：挂号、缴费、取药等。"
    Listen 5, 20
    Branch "挂号", registration
    Branch "缴费", payment
    Branch "取药", pharmacy
    Branch "查询", query
    Silence goodbye
    Default welcome

Step defaultHandler
    Speak "抱歉，我没有理解您的意思。您可以说：挂号、缴费、取药、查询 或 人工服务。请问需要什么帮助？"
    Listen 5, 20
    Branch "挂号", registration
    Branch "缴费", payment
    Branch "取药", pharmacy
    Branch "查询", query
    Branch "人工服务", humanService
    Default welcome

Step goodbye
    Speak "感谢您使用XX医院智能客服系统，祝您身体健康！再见！"
    Exit
