"""Reproduce the handbook's synthetic car-wash experiment; Python 3, no packages.

Run: python car-wash-reference.py > car-wash-results.json
This finite reference fixture is not the Aura Pro product simulator.
All inputs are illustrative. No measured data or fitted probabilities are used.
"""
import heapq
import json


def run(policy, failure=True, attendant_available=0, *, initial_stock=12,
        work_priority="repair_first", first_check_fails=False):
    events, trace, queue = [], [], []
    counter = 0
    bays = {i: {"state": "ready", "car": None, "attempt": 0}
            for i in (1, 2, 3)}
    cars = {i: {"arrival": 2 * (i - 1), "first_start": None,
                "finish": None, "bay": None} for i in range(1, 11)}
    stock, used, reserved = initial_stock, 0, 0
    release_time = None
    service_requested = False
    service_started = False
    receiving_pending = False
    received = False
    attendant_busy = False
    specialist_present = False
    specialist_started = False
    specialist_part_stock = 0
    specialist_parts_used = 0
    attendant_intervals = []
    specialist_intervals = []
    stock_accepted_time = None
    failed_check_time = None

    def schedule(time, priority, kind, data=None):
        nonlocal counter
        counter += 1
        heapq.heappush(events, (time, priority, counter, kind, data))

    def note(time, message):
        trace.append({"minute": time, "event": message,
                      "usable_stock": stock, "reserved_for_test": reserved,
                      "consumed_units": used})

    def consume():
        nonlocal stock, used
        assert stock >= 1
        stock -= 1
        used += 1

    def start(time, bay_id, car_id):
        bay = bays[bay_id]
        consume()
        bay.update(state="washing", car=car_id, attempt=bay["attempt"] + 1)
        if cars[car_id]["first_start"] is None:
            cars[car_id].update(first_start=time, bay=bay_id)
        schedule(time + 6, 0, "finish", (bay_id, car_id, bay["attempt"]))
        note(time, f"Car {car_id} starts a full wash in bay {bay_id}")

    def request_service(time):
        nonlocal service_requested
        if bays[2]["state"] == "failed" and not service_requested:
            service_requested = True
            note(time, f"Lead requests diagnosis; attendant available from {attendant_available}")

    def reserve_test():
        nonlocal stock, reserved
        assert stock >= 1
        stock -= 1
        reserved += 1

    def use_test():
        nonlocal reserved, used
        assert reserved >= 1
        reserved -= 1
        used += 1

    def dispatch_workers(time):
        nonlocal attendant_busy, receiving_pending, service_started
        nonlocal specialist_started
        if not attendant_busy and time >= attendant_available:
            repair_ready = service_requested and not service_started and stock > 0
            # The lead may reserve the attendant for the reported minute-20
            # delivery until minute 22, rather than starting non-preemptible work.
            hold_for_receiving = (work_priority == "receive_first" and
                                  not received and not receiving_pending and time < 22)
            choose_receiving = receiving_pending and (
                work_priority == "receive_first" or not repair_ready)
            if choose_receiving:
                receiving_pending = False
                attendant_busy = True
                attendant_intervals.append([time, time + 2, "receiving"])
                note(time, "Attendant starts receiving; delivered stock is not usable yet")
                schedule(time + 2, 0, "stock")
            elif repair_ready and not hold_for_receiving:
                service_started = True
                attendant_busy = True
                reserve_test()
                bays[2]["state"] = "diagnosis"
                attendant_intervals.append([time, time + 5, "diagnosis, repair, test"])
                note(time, "Attendant begins diagnosis; one test dose reserved")
                schedule(time + 1, 2, "repair")
        if (specialist_present and not specialist_started and stock > 0):
            specialist_started = True
            reserve_test()
            bays[2]["state"] = "specialist_diagnosis"
            specialist_intervals.append([time, time + 7, "diagnosis, component replacement, retest"])
            note(time, "Specialist begins new diagnosis; retest dose reserved")
            schedule(time + 2, 2, "specialist_replace")

    for car, record in cars.items():
        schedule(record["arrival"], 1, "arrival", car)
    if failure:
        schedule(5, -1, "failure")
        schedule(7, 2, "report")
    schedule(12, 2, "review")
    schedule(20, 1, "delivery")
    if attendant_available:
        schedule(attendant_available, 2, "attendant_available")
    if work_priority == "receive_first":
        schedule(22, 2, "hold_deadline")

    while events:
        time = events[0][0]
        # Process all same-time events before allocating free bays. Physical
        # changes precede arrivals and information; dispatch is the last phase.
        while events and events[0][0] == time:
            _, _, _, kind, data = heapq.heappop(events)
            if kind == "arrival":
                queue.append(data)
                note(time, f"Car {data} arrives")
            elif kind == "failure":
                assert bays[2]["car"] == 2 and bays[2]["state"] == "washing"
                bays[2]["state"] = "failed"
                bays[2]["attempt"] += 1  # Invalidate the old completion event.
                note(time, "Bay 2 stops locally; car 2 retained; no staff report yet")
            elif kind == "report":
                note(time, "Fault report reaches AP; cause remains unconfirmed")
                if policy == "prompt":
                    request_service(time)
            elif kind == "review":
                note(time, "Scheduled operating review")
                request_service(time)
            elif kind == "repair":
                bays[2]["state"] = "repair"
                note(time, "Diagnosis supports the modeled minor repair; repair starts")
                schedule(time + 3, 2, "test")
            elif kind == "test":
                use_test()
                bays[2]["state"] = "testing"
                note(time, "Repair complete; one-minute functional test starts")
                schedule(time + 1, 2, "accept")
            elif kind == "accept":
                attendant_busy = False
                if first_check_fails:
                    failed_check_time = time
                    bays[2]["state"] = "awaiting_specialist"
                    note(time, "Functional check fails; lead holds bay and requests specialist inquiry")
                    schedule(time + 4, 1, "specialist_arrives")
                else:
                    bays[2]["state"] = "restart_pending"
                    release_time = time
                    note(time, "Functional test passes; authorized lead releases bay 2")
            elif kind == "specialist_arrives":
                specialist_present = True
                specialist_part_stock = 1
                note(time, "Booked specialist arrives with identified replacement part")
            elif kind == "specialist_replace":
                assert specialist_part_stock == 1
                specialist_part_stock -= 1
                specialist_parts_used += 1
                bays[2]["state"] = "component_replacement"
                note(time, "New diagnosis supports component replacement; authorized method replaces minor repair")
                schedule(time + 4, 2, "specialist_test")
            elif kind == "specialist_test":
                use_test()
                bays[2]["state"] = "specialist_testing"
                note(time, "Replacement complete; specialist starts retest")
                schedule(time + 1, 2, "specialist_accept")
            elif kind == "specialist_accept":
                bays[2]["state"] = "restart_pending"
                release_time = time
                note(time, "Retest passes; lead accepts result and releases bay 2")
            elif kind == "finish":
                bay_id, car_id, attempt = data
                bay = bays[bay_id]
                if bay["state"] != "washing" or attempt != bay["attempt"]:
                    continue
                cars[car_id]["finish"] = time
                bay.update(state="ready", car=None)
                note(time, f"Car {car_id} completes and leaves bay {bay_id}")
            elif kind == "delivery":
                # Delivery is reported at 20; six units become usable only
                # after the attendant's two-minute identity/quantity check.
                receiving_pending = True
                note(time, "Six supply units arrive; receiving job enters attendant queue")
            elif kind == "stock":
                stock += 6
                received = True
                attendant_busy = False
                stock_accepted_time = time
                note(time, "Six supply units accepted into usable stock")
            elif kind == "attendant_available":
                note(time, "Attendant released from prior work")
            elif kind == "hold_deadline":
                note(time, "Receiving hold deadline; evaluate currently ready jobs")
        dispatch_workers(time)
        # The interrupted customer's restart precedes admission of new work.
        if bays[2]["state"] == "restart_pending" and stock:
            start(time, 2, 2)
        for bay_id in (1, 2, 3):
            if bays[bay_id]["state"] == "ready" and queue and stock:
                start(time, bay_id, queue.pop(0))
        assert stock >= 0 and reserved >= 0
        assert stock + reserved + used == initial_stock + (6 if received else 0)
        active = [b["car"] for b in bays.values() if b["car"] is not None]
        assert len(active) == len(set(active))

    assert all(c["finish"] is not None for c in cars.values())
    assert stock == initial_stock + 6 - used and reserved == 0
    assert specialist_part_stock + specialist_parts_used == int(specialist_present)
    if first_check_fails and failure:
        assert failed_check_time is not None and release_time > failed_check_time
        assert specialist_parts_used == 1
    for i, (a, z, _) in enumerate(attendant_intervals):
        assert a >= attendant_available
        assert all(z <= b or y <= a for b, y, _ in attendant_intervals[i + 1:])
    waits = [c["first_start"] - c["arrival"] for c in cars.values()]
    return {
        "policy": policy, "failure_at_minute_5": failure,
        "attendant_available_from": attendant_available,
        "summary": {
            "completed_by_minute_24": sum(c["finish"] <= 24 for c in cars.values()),
            "all_complete_at": max(c["finish"] for c in cars.values()),
            "initial_queue_wait_minutes_total": sum(waits),
            "initial_queue_wait_minutes_mean": sum(waits) / len(waits),
            "customer_minutes_on_site_total": sum(c["finish"] - c["arrival"] for c in cars.values()),
            "car_2_complete_at": cars[2]["finish"],
            "bay_2_released_at": release_time,
            "attendant_minutes": sum(z - a for a, z, _ in attendant_intervals),
            "supply_units_used": used, "supply_units_remaining": stock,
        },
        "customers": cars, "attendant_intervals": attendant_intervals, "trace": trace,
        "decision_inputs": {"initial_stock": initial_stock, "work_priority": work_priority,
                            "first_check_fails": first_check_fails,
                            "reported_delivery_time": 20, "receiving_hold_deadline": 22},
        "recovery": {"stock_accepted_at": stock_accepted_time,
                     "failed_check_at": failed_check_time,
                     "specialist_intervals": specialist_intervals,
                     "specialist_parts_received": int(specialist_present),
                     "specialist_parts_used": specialist_parts_used,
                     "specialist_part_stock": specialist_part_stock},
    }


def experiment():
    cases = [("No failure", False, 0), ("Failure; attendant available", True, 0),
             ("Failure; attendant occupied until minute 14", True, 14)]
    results = [{"case": name, **run(policy, failure, available)}
               for name, failure, available in cases for policy in ("routine", "prompt")]
    normal = results[:2]
    assert normal[0]["summary"] == normal[1]["summary"]
    routine, prompt = results[2:4]
    assert routine["summary"]["initial_queue_wait_minutes_total"] == 23
    assert prompt["summary"]["initial_queue_wait_minutes_total"] == 18
    assert routine["summary"]["all_complete_at"] == 29
    assert prompt["summary"]["all_complete_at"] == 28
    assert results[4]["summary"] == results[5]["summary"]
    decisions = [{"case": label, **run("prompt", True, 18, initial_stock=8,
                                       work_priority=priority, first_check_fails=failed)}
                 for label, priority, failed in [
                     ("Limited stock; repair first", "repair_first", False),
                     ("Limited stock; receive first", "receive_first", False),
                     ("Limited stock; receive first; failed functional check", "receive_first", True)]]
    resource_regression = run("prompt", True, 18)
    assert resource_regression["recovery"]["stock_accepted_at"] == 25
    repair, receive, failed = decisions
    assert repair["recovery"]["stock_accepted_at"] == 25
    assert receive["recovery"]["stock_accepted_at"] == 22
    assert repair["summary"]["customer_minutes_on_site_total"] == 124
    assert receive["summary"]["customer_minutes_on_site_total"] == 109
    assert failed["recovery"]["failed_check_at"] == 27
    assert failed["summary"]["bay_2_released_at"] == 38
    assert failed["summary"]["car_2_complete_at"] == 44
    assert max(c["finish"] for i, c in failed["customers"].items() if i != 2) == 30
    return {"status": "Synthetic reference runs, not operational validation",
            "model_version": "car-wash-reference-2",
            "common_inputs": {
                "time_unit": "minute", "ready_bays_at_start": [1, 2, 3],
                "arrival_times": list(range(0, 20, 2)), "wash_duration": 6,
                "failure_bay": 2, "failure_time_when_enabled": 5,
                "fault_report_time": 7, "routine_review_time": 12,
                "diagnosis_duration": 1, "repair_duration": 3, "test_duration": 1,
                "test_outcome": "pass", "release_review_delay": 0,
                "initial_supply_units": 12, "delivery_time": 20,
                "delivery_units": 6, "receiving_duration": 2,
                "units_per_wash_start_or_test": 1,
                "interrupted_wash": "retain customer; cancel completion; full restart",
                "queue": "FIFO; lowest-numbered ready bay; interrupted customer retains bay",
                "same_time_phases": ["failure", "completion or accepted stock",
                                     "arrival", "information and decisions", "dispatch"],
                "abandonment": False, "scenario_probabilities": None,
                "test_dose_policy": "reserve one usable unit when a recovery job starts; consume at test",
                "attendant_allocation": "queued non-preemptible jobs; readiness and selected priority determine start",
                "specialist_assumptions_if_first_check_fails": {
                    "response_interval": 4, "diagnosis": 2, "replacement": 4,
                    "retest": 1, "available_parts": 1, "retest_result": "pass",
                    "authorization_review_delay": 0},
            }, "runs": results, "decision_runs": decisions,
            "resource_conflict_check": resource_regression,
            "parent_readiness": [
                {"case": "Other prerequisites ready by day 25", "before": max(26, 25, 25),
                 "after": max(25, 25, 25), "booked_test_retained_after": True},
                {"case": "External controls ready on day 26", "before": max(26, 26, 25),
                 "after": max(25, 26, 25), "booked_test_retained_after": False},
            ]}


if __name__ == "__main__":
    print(json.dumps(experiment(), indent=2))
