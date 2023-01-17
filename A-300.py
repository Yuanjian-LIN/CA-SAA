import cv2
import random
import numba as nb
import numpy as np
import concurrent.futures

# 根据两点法 和 线段法  计算，
# 这是根据 二维图片 获取对应的 两点法 和 线段法的比率
@nb.jit(nopython=True)
def obtain_line_and_point(pic_array, sample_time, size_gap):
    row, column = pic_array.shape
    size_list = []
    point_list = []
    line_list = []
    for size in range(0, 51, size_gap):
        size_list.append(size)
        count_two_point = 0
        count_two_line = 0
        for i in range(sample_time):
            flag = 0
            while flag == 0:
                start_i = random.randint(0, row-1)
                start_j = random.randint(0, column-1)
                angle = random.randint(0, 361)
                end_i = int(start_i + size * np.cos(angle * 3.14 / 180))
                end_j = int(start_j + size * np.sin(angle * 3.14 / 180))
                if 0 <= int(end_i) < row and 0 <= int(end_j) < column:
                    flag = 1
#             两点法
            if pic_array[start_i][start_j] == 255 and pic_array[end_i][end_j] == 255:
                count_two_point += 1
        #     线段法
            i_in_line = np.linspace(start_i, end_i, 200)
            j_in_line = np.linspace(start_j, end_j, 200)
            temp_flag = 1
            for i in range(len(i_in_line)):
                x = i_in_line[i]
                y = j_in_line[i]
                if pic_array[int(x)][int(y)] == 0:
                    temp_flag = 0
                    break
            if temp_flag == 1:
                count_two_line += 1
        point_list.append(count_two_point/sample_time)
        line_list.append(count_two_line/sample_time)
    return size_list, point_list, line_list


# 根据两点法 和 线段法  计算
# 这是计算 构建的三维 裂隙模型的 两点法 及 线段法的 比率
@nb.jit(nopython=True)
def obtain_line_and_point_three_dimension(pic_array_3D, sample_time, size_gap):
    pic_number, row, column = pic_array_3D.shape
    size_list = []
    point_list = []
    line_list = []
    for size in range(0, 51, size_gap):
        size_list.append(size)
        count_two_point = 0
        count_two_line = 0
        for i in range(sample_time):
            flag = 0
            while flag == 0:
                start_i = random.randint(0, pic_number-1)
                start_j = random.randint(0, row-1)
                start_k = random.randint(0, column-1)
                angle_1 = random.randint(0, 361)
                angle_2 = random.randint(0, 361)
                end_i = int(start_i + size * np.cos(angle_2 * 3.14 / 180) * np.cos(angle_1 * 3.14 / 180))
                end_j = int(start_j + size * np.cos(angle_2 * 3.14 / 180) * np.sin(angle_1 * 3.14 / 180))
                end_k = int(start_k  + size * np.sin(angle_2 * 3.14 / 180))
                if 0 <= int(end_i) < pic_number and 0 <= int(end_j) < row and 0 <= int(end_k) < column:
                    flag = 1
#             两点法
            if pic_array_3D[start_i,start_j, start_k] == 255 and pic_array_3D[end_i, end_j, end_k] == 255:
                count_two_point += 1
        #     线段法
            i_in_line = np.linspace(start_i, end_i, 200)
            j_in_line = np.linspace(start_j, end_j, 200)
            k_in_line = np.linspace(start_k, end_k, 200)
            temp_flag = 1
            for i in range(len(i_in_line)):
                x = i_in_line[i]
                y = j_in_line[i]
                z = k_in_line[i]
                if pic_array_3D[int(x),int(y), int(z)] == 0:
                    temp_flag = 0
                    break
            if temp_flag == 1:
                count_two_line += 1
        point_list.append(count_two_point/sample_time)
        line_list.append(count_two_line/sample_time)
    return size_list, point_list, line_list

def point_line_error(two_point, two_line, new_point, new_line):
    point_error_list = []
    line_error_list = []
    for i in range(len(two_point)):
        point_error_list.append(abs((two_point[i] - new_point[i]) / two_point[i]))
        line_error_list.append(abs((two_line[i] - new_line[i]) / two_line[i]))
    max_point_error = np.mean(point_error_list)
    max_line_error = np.mean(line_error_list)
    max_error = max(max_line_error, max_point_error)
    return max_error, max_point_error, max_line_error


def initial_pic(pic_number, row, column, ratio):
    new_pic = np.zeros([pic_number, row, column], dtype=np.uint8)
    for i in range(pic_number):
        for j in range(column):
            for k in range(column):
                if random.random() < ratio:
                    new_pic[i, j, k] = 255
    return new_pic

@nb.jit(nopython=True)
def surround_pic_number(number, i, j, k, pic_3D, pic_number, pic_row, pic_column):
    count = 0
    for x in [i-1, i, i+1]:
        for y in [j-1, j, j+1]:
            for z in [k-1, k, k+1]:
                if 0 <= x <= pic_number-1 and 0 <= y <= pic_row-1 and 0 <= z <= pic_column-1:
                    if pic_3D[x, y, z] == number:
                        count += 1
    return count

@nb.jit(nopython=True)
def change_to_255(pic_number, row, column, pic_3D, critical_zone_number):
    flag = 0
    while flag == 0:
        pic_i = random.randint(0, pic_number-1)
        pic_j = random.randint(0, row-1)
        pic_k = random.randint(0, column-1)
        if pic_3D[pic_i,pic_j,pic_k] == 0:
            count = surround_pic_number(255, pic_i,pic_j, pic_k, pic_3D, pic_number, row, column)
            if count >= critical_zone_number:
                pic_3D[pic_i, pic_j, pic_k] = 255
                flag = 1
    return pic_3D

@nb.jit(nopython=True)
def change_to_0(pic_number, row, column, pic_3D, critical_zone_number):
    flag = 0
    while flag == 0:
        pic_i = random.randint(0, pic_number - 1)
        pic_j = random.randint(0, row - 1)
        pic_k = random.randint(0, column - 1)
        if pic_3D[pic_i,pic_j, pic_k] == 255:
            count = surround_pic_number(0, pic_i,pic_j, pic_k, pic_3D, pic_number, row, column)
            if count >= critical_zone_number:
                pic_3D[pic_i, pic_j, pic_k] = 0
                flag = 1
    return pic_3D

@nb.jit(nopython=True)
def change_two_point(pic_number, row, column, pic_3D, change_time, critical_zone_number):
    for i in range(change_time):
        pic_3D = change_to_255(pic_number, row, column, pic_3D, critical_zone_number)
        pic_3D = change_to_0(pic_number, row, column, pic_3D, critical_zone_number)
    return pic_3D

# 单线程产生下一个
def generate_next_pic_and_calculate(pic_number, new_row, new_column, pre_pic, change_time, sample_time, point_list_origin, line_list_origin, critical_zone_number, size_gap):
    next_pic = change_two_point(pic_number, new_row, new_column, pre_pic, change_time, critical_zone_number)
    size_list, point_list, line_list = obtain_line_and_point_three_dimension(next_pic, sample_time, size_gap)
    max_error, max_point_error, max_line_error = point_line_error(point_list_origin, line_list_origin, point_list, line_list)
    next_judge = max_error
    return next_pic, next_judge, size_list, point_list, line_list

# 多线程并行产生 并计算
def parallel_generate_pic_and_calculate(pic_number, new_row, new_column, pre_pic, change_time, sample_time, point_list_origin, line_list_origin, process_number, critical_zone_number, size_gap):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        generate_pic_calculate = []
        all_result = []
        for i in range(process_number):
            generate_pic_calculate.append(executor.submit(generate_next_pic_and_calculate, pic_number, new_row, new_column, pre_pic, change_time, sample_time, point_list_origin, line_list_origin, critical_zone_number, size_gap))
        for calculate in generate_pic_calculate:
            all_result.append(calculate.result())
    min_value = np.inf
    for i in range(process_number):
        if all_result[i][1] < min_value:
            out_pic = all_result[i][0].copy()
            min_value = all_result[i][1]
            size_list = all_result[i][2]
            point_list = all_result[i][3]
            line_list = all_result[i][4]
    return min_value, out_pic, size_list, point_list, line_list


def main_program(origin_pic, pic_number, pic_row, pic_column, change_time, critical_zone_number, sample_time, process_number, size_gap):
    img = cv2.imread(origin_pic)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    row, column = gray.shape
    size_list, point_list_origin, line_list_origin = obtain_line_and_point(gray, 10000, size_gap)
    print('原始图片的相关信息：')
    print(size_list)
    print(point_list_origin)
    print(line_list_origin)
    file = open('300\\原始图片信息.txt', 'w')
    file.write('size   point  line \n')
    for i in range(len(size_list)):
        file.write('%r   %r   %r  \n' %( size_list[i], point_list_origin[i], line_list_origin[i]))
    file.close()

    count_pore = 0
    for i in range(row):
        for j in range(column):
            if gray[i][j] == 255:
                count_pore += 1
    ratio = count_pore / (row * column)

    new_row, new_column = pic_row, pic_column

    # 模拟退火算法的基本参数
    markovlength = 10000  # 每次降温迭代次数，建议为5或者10
    decayscale = 0.99
    temperature = 100

    pre_pic = initial_pic(pic_number, new_row, new_column, ratio)
    size_list, point_list, line_list = obtain_line_and_point_three_dimension(pre_pic, sample_time, size_gap)
    max_error, max_point_error, max_line_error = point_line_error(point_list_origin, line_list_origin, point_list, line_list)


    pre_judge = max_error
    best_judge = pre_judge
    best_pic = pre_pic.copy()

    for i in range(10000):
        temperature *= decayscale
        for i in range(markovlength):
            next_judge, next_pic, size_list, point_list, line_list = parallel_generate_pic_and_calculate(pic_number, new_row, new_column, pre_pic, change_time, sample_time, point_list_origin, line_list_origin, process_number, critical_zone_number, size_gap)
            # 第 2 处需要修改
            # 求最大值就是:  >   求最小值就是:  <
            if next_judge < best_judge:
                best_pic = next_pic.copy()
                best_judge = next_judge
                print('======================================================')
                print('误差为：')
                print(best_judge)
                print('测量尺度为')
                print(size_list)
                print('两点法结果为：')
                print(point_list)
                print('线段法结果为')
                print(line_list)
                print('======================================================')
                file = open('300\\point-line.txt', 'w')
                file.write('误差为：%r \n' % best_judge)
                file.write('size  point  line \n')
                for i in range(len(size_list)):
                    file.write('%r   %r   %r  \n' % (size_list[i], point_list[i], line_list[i]))
                file.close()

                # 将最好的结果自动 更新，并替换图片
                for i in range(pic_number):
                    temp_pic = np.zeros([pic_row, pic_column], dtype=np.uint8)
                    for j in range(pic_row):
                        for k in range(pic_column):
                            temp_pic[j][k] = best_pic[i, j, k]
                    pic_name = '300\\%d.tif' % i
                    cv2.imwrite(pic_name, temp_pic)
            # 第 3 处需要修改
            # 求最大值就是:  >   求最小值就是:  <
            if next_judge < pre_judge:
                pre_pic = next_pic.copy()
                pre_judge = next_judge
            else:
                changer = -abs(next_judge - pre_judge) / temperature
                rnd = random.random()
                p1 = np.exp(changer)
                if p1 > rnd:
                    pre_pic = next_pic.copy()
                    pre_judge = next_judge

# 这个__name__ == '__main__'  一定要加，不然在concurrent并行运算的模块中会出错
if __name__ == '__main__':
    # 产生图片的数量
    pic_number = 300
    # 图片的row大小
    pic_row = 300
    # 图片column大小
    pic_column = 300
    # 目标图像，就是以该图像为基准生成图像
    target_pic = '4.tif'
    # 周围有多少 个 临界点，就开始转换，总共 有 26个
    critical_zone_number = 8
    # 每次细胞自动机运动次数，每次运动次数越小，生成图片越精细，但收敛速度越慢
    change_time = int(pic_number * pic_row * pic_column / 30)
    # 线段法 和 两点法 测量比率 测量次数
    # 测量次数越多，计算越慢
    sample_time = 10000
    # 并行运行程序个数
    process_number = 10
    # 两点法，线段法测量 间距  0 2 4
    size_gap = 1
    main_program(target_pic, pic_number, pic_row,  pic_column, change_time, critical_zone_number, sample_time, process_number, size_gap)
