def is_polygon_contains_point(
    points: list[dict[str, float]], ra: float, dec: float
) -> bool:
    result: bool = False
    for i in range(len(points)):
        if (
            (points[i]["dec"] <= dec and dec < points[i - 1]["dec"])
            or (points[i - 1]["dec"] <= dec and dec < points[i]["dec"])
        ) and (
            ra
            > (points[i - 1]["ra"] - points[i]["ra"])
            * (dec - points[i]["dec"])
            / (points[i - 1]["dec"] - points[i]["dec"])
            + points[i]["ra"]
        ):
            result = not result
    return result


def is_points_range_valid(points: list[dict[str, float]]) -> bool:
    for point in points:
        if not (-24 < point["ra"] < 24 and -90 <= point["dec"] <= 90):
            return False

    return True


def Graham_scan(points: list[dict[str, float]]) -> list[dict[str, float]]:
    def is_right_rotate(
        a: dict[str, float], b: dict[str, float], c: dict[str, float]
    ) -> bool:
        result = (b["ra"] - a["ra"]) * (c["dec"] - b["dec"]) - (b["dec"] - a["dec"]) * (
            c["ra"] - b["ra"]
        )
        if result < 0:
            return True
        else:
            return False

    length: int = len(points)

    for i in range(1, length):
        if points[0]["dec"] > points[i]["dec"]:
            points[0], points[i] = points[i], points[0]

    for i in range(2, length):
        j = i
        while j > 1 and is_right_rotate(points[0], points[j - 1], points[j]):
            points[j], points[j - 1] = points[j - 1], points[j]
            j -= 1

    answer: list[dict[str, float]] = [points[0], points[1]]
    for i in range(2, length):
        while is_right_rotate(answer[-2], answer[-1], points[i]):
            del answer[-1]
        answer.append(points[i])

    return answer
