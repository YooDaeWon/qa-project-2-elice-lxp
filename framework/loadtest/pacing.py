import random
import time

RAMP_UP_SECONDS = 1.0
THINK_TIME_MIN = 3.0
THINK_TIME_MAX = 5.0
LAST_STAGE_USERS = 30


def ramp_up_wait(user_index, user_count, ramp_up_seconds=RAMP_UP_SECONDS):
    """JMeter Ramp-up과 같이 가상 유저 기동을 분산한다."""
    if user_count <= 1 or ramp_up_seconds <= 0:
        return
    delay = user_index * (ramp_up_seconds / user_count)
    if delay > 0:
        time.sleep(delay)


def think_time(min_seconds=THINK_TIME_MIN, max_seconds=THINK_TIME_MAX):
    """실사용자 클릭 간격을 모사하는 Timer."""
    time.sleep(random.uniform(min_seconds, max_seconds))


def pause_after_stage(user_count, last_stage=LAST_STAGE_USERS):
    """5 → 10 → 20 → 30 단계 사이에 대기를 둔다. 마지막 단계는 생략한다."""
    if user_count == last_stage:
        return
    print(
        f"  └ ⏳ 다음 단계 전 think time {THINK_TIME_MIN:.0f}~{THINK_TIME_MAX:.0f}초"
    )
    think_time()
