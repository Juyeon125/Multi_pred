def fun():
    ec_list = ["3.1.2.5", "3.1.2.5", "1.2.2.2"]
    acc_list = [90.1, 76.7, 78.5]
    s_list = []
    re_list = []

    # S값 구하기
    for i in ec_list:
        cnt = ec_list.count(i)
        s_list.append(cnt / 3)

    print(s_list)

    # R값 구하기
    for i in range(len(ec_list)):
        temp = s_list[i] * acc_list[i]
        re_list.append(temp)

    sum_relist = sum(re_list)
    finre_list = []

    for i in range(len(ec_list)):
        temp = re_list[i]/sum_relist
        finre_list.append(round(temp, 3))

    print(finre_list)

    for v in range(0, len(ec_list)):
        if (v == re_list.index(max(re_list))):
            final_result = ec_list[v]

    print("DeepEC -> EC number :", ec_list[0], "Accuracy :", acc_list[0])
    print("ECPred -> EC number :", ec_list[1], "Accuracy :", acc_list[1])
    print("DETECTv2 -> EC number :", ec_list[2], "Accuracy :", acc_list[2])

    print("We recommend", final_result)