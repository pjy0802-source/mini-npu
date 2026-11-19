import json
import math
import re
from pathlib import Path
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


def manual_mode():
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


def validate_matrix(matrix, size, name):
    if not isinstance(matrix, list) or len(matrix) != size:
        raise ValueError(f"{name}: 행이 {size}개여야 합니다.")

    for row_number, row in enumerate(matrix, start=1):
        if not isinstance(row, list) or len(row) != size:
            raise ValueError(f"{name}: {row_number}행에 값이 {size}개여야 합니다.")

        for value in row:
            if type(value) not in (int, float):
                raise ValueError(f"{name}: {row_number}행에 숫자가 아닌 값이 있습니다.")
            if not math.isfinite(value):
                raise ValueError(f"{name}: {row_number}행에 유한한 숫자가 필요합니다.")


def normalize_label(raw_label):
    """필터 키와 기대 라벨을 공통 표준 이름으로 변환한다."""
    aliases = {"+": "Cross", "cross": "Cross", "x": "X"}
    if not isinstance(raw_label, str):
        raise ValueError("라벨은 문자열이어야 합니다.")

    label = aliases.get(raw_label.strip().lower())
    if label is None:
        raise ValueError(f"알 수 없는 라벨: {raw_label!r}")
    return label


def json_mode():
    data_path = Path(__file__).with_name("data.json")

    try:
        with data_path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("main.py와 같은 폴더에 data.json을 넣어주세요.")
        return
    except (OSError, ValueError) as error:
        print(f"data.json 읽기 오류: {error}")
        return

    if not isinstance(data, dict) or not isinstance(data.get("patterns"), dict):
        print("JSON 형식 오류: patterns 객체가 필요합니다.")
        return

    patterns = data["patterns"]
    filter_groups = data.get("filters")
    if not isinstance(filter_groups, dict):
        filter_groups = {}

    epsilon = 1e-9
    passed = 0
    failed_cases = {}

    for case_name, case in patterns.items():
        print(f"\n[{case_name}]")

        try:
            match = re.fullmatch(r"size_(5|13|25)_[0-9]+", case_name)
            if match is None:
                raise ValueError("패턴 이름 형식이 잘못됐습니다.")

            size = int(match.group(1))
            filter_key = f"size_{size}"
            raw_filters = filter_groups.get(filter_key)

            if not isinstance(raw_filters, dict):
                raise ValueError(f"{filter_key} 필터 그룹이 없거나 형식이 잘못됐습니다.")

            filters = {}
            for raw_label, matrix in raw_filters.items():
                label = normalize_label(raw_label)
                if label in filters:
                    raise ValueError(f"중복된 필터 라벨: {raw_label}")
                validate_matrix(matrix, size, f"{filter_key}.{label}")
                filters[label] = matrix

            if set(filters) != {"Cross", "X"}:
                raise ValueError("Cross 필터와 X 필터가 모두 필요합니다.")

            if not isinstance(case, dict) or "input" not in case:
                raise ValueError("패턴에 input이 필요합니다.")

            expected = normalize_label(case.get("expected"))

            pattern = case["input"]
            validate_matrix(pattern, size, "입력 패턴")
            cross_score = mac(pattern, filters["Cross"])
            x_score = mac(pattern, filters["X"])

            if not (math.isfinite(cross_score) and math.isfinite(x_score)):
                raise ValueError("MAC 점수가 계산 가능한 숫자 범위를 벗어났습니다.")

        except (ValueError, OverflowError) as error:
            failed_cases[case_name] = str(error)
            print(f"FAIL | 사유: {error}")
            continue

        difference = abs(cross_score - x_score)
        if difference < epsilon:
            prediction = "UNDECIDED"
        elif cross_score > x_score:
            prediction = "Cross"
        else:
            prediction = "X"

        print(f"Cross 점수: {cross_score}")
        print(f"X 점수: {x_score}")

        if prediction == expected:
            passed += 1
            print(f"기대 라벨: {expected} | 판정: {prediction} | PASS")
        else:
            reason = f"기대 라벨 {expected}, 실제 판정 {prediction}"
            if prediction == "UNDECIDED":
                reason += f" (동점: 점수 차이 {difference:.3g} < {epsilon:g})"

            failed_cases[case_name] = reason
            print(f"FAIL | 사유: {reason}")
    print("\n[크기별 MAC 성능 분석: 10회 평균]")
    print("크기     평균 시간(ms)    MAC 횟수")

    for size in (3, 5, 13, 25):
        matrix = [[1.0] * size for _ in range(size)]
        average_ms = measure_mac_ms(matrix, matrix)
        print(f"{size}×{size:<4} {average_ms:>13.6f} {size * size:>11}")
    print("\n[결과 요약]")
    print(f"전체: {len(patterns)}개")    
    print(f"통과: {passed}개")
    print(f"실패: {len(failed_cases)}개")

    for case_name, reason in failed_cases.items():
        print(f"- {case_name}: {reason}")


def main():
    print("Mini NPU Simulator 시작")
    print("1. 사용자 입력 (3×3)")
    print("2. data.json 분석")

    choice = input("선택: ").strip()
    if choice == "1":
        manual_mode()
    elif choice == "2":
        json_mode()
    else:
        print("1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
