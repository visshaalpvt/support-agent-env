def clamp_score(x):
    if x <= 0.0:
        return 0.01
    if x >= 1.0:
        return 0.99
    return round(x, 3)

def grade_easy(cat, truth):
    if cat == truth:
        return clamp_score(1.0), "Correct"
    return clamp_score(0.0), "Wrong"

def grade_medium(cat, truth, pri, truth_pri):
    cat_score = 0.495 if cat == truth else 0.01
    pri_score = 0.495 if pri == truth_pri else 0.01
    return clamp_score(cat_score + pri_score), "Medium result", pri_score

def grade_hard(cat, truth, pri, truth_pri, resp, keywords):
    cat_score = 0.33 if cat == truth else 0.01
    pri_score = 0.33 if pri == truth_pri else 0.01
    resp_score = 0.33 if resp and len(resp) > 5 else 0.01
    return clamp_score(cat_score + pri_score + resp_score), "Hard result", pri_score, resp_score

def get_grader(diff):
    if diff == "easy":
        return grade_easy
    elif diff == "medium":
        return grade_medium
    return grade_hard
