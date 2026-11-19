from time import perf_counter
def mac(pattern, filter_matrix):
    total = 0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_matrix[row][col]

    return total
def measure_mac_ms(pattern, filter_matrix):
    total_seconds = 0.0

    for _ in range(10):
        start = perf_counter()
        mac(pattern, filter_matrix)
        total_seconds += perf_counter() - start

    return (total_seconds / 10) * 1000

def read_matrix(name):
    print(f"{name}을 입력하세요. 한 줄에 숫자 3개를 공백으로 구분하세요.")
    matrix = []

    while len(matrix) < 3:
        values = input(f"{len(matrix) + 1}행: ").split()

        if len(values) != 3:
            print("숫자 3개를 입력하세요.")
            continue

        try:
            row = [float(value) for value in values]
        except ValueError:
            print("숫자만 입력하세요.")
            continue

        matrix.append(row)

    return matrix

print("mini npu simulator 시작")


cross_filter = read_matrix("필터 A")
x_filter = read_matrix("필터 B")

print("필터 A와 B를 저장했습니다.")

pattern = read_matrix("패턴")

score = mac(pattern, cross_filter)
x_score = mac(pattern, x_filter)

print(f"A 점수: {score}")
print(f"B 점수: {x_score}")

epsilon = 1e-9

if abs(score - x_score) < epsilon:
    print("판정: 판정 불가")
elif score > x_score:
    print("판정: A")
else:
    print("판정: B")
average_ms = measure_mac_ms(pattern, cross_filter)

print("\n[성능 분석: 필터 A, 10회 평균]")
print("크기   평균 시간(ms)   MAC 횟수")
print(f"3×3    {average_ms:.6f}          9")