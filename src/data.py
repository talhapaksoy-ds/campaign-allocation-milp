# data_generator.py

def get_test_instance():
    """
    Returns a small synthetic test instance for the
    Marketing Campaign Budget Allocation problem.
    """

    campaigns = [
        {"id": "C1",  "channel": "Social", "cost": 12, "roi": 20, "risk": 4, "reach": 90},
        {"id": "C2",  "channel": "Social", "cost": 18, "roi": 28, "risk": 6, "reach": 130},
        {"id": "C3",  "channel": "Search", "cost": 15, "roi": 24, "risk": 5, "reach": 110},
        {"id": "C4",  "channel": "Search", "cost": 20, "roi": 31, "risk": 7, "reach": 150},
        {"id": "C5",  "channel": "Email",  "cost": 8,  "roi": 14, "risk": 2, "reach": 70},
        {"id": "C6",  "channel": "Email",  "cost": 10, "roi": 16, "risk": 3, "reach": 85},
        {"id": "C7",  "channel": "TV",     "cost": 30, "roi": 40, "risk": 9, "reach": 220},
        {"id": "C8",  "channel": "Social", "cost": 14, "roi": 21, "risk": 5, "reach": 100},
        {"id": "C9",  "channel": "Search", "cost": 16, "roi": 25, "risk": 4, "reach": 120},
        {"id": "C10", "channel": "Email",  "cost": 9,  "roi": 15, "risk": 2, "reach": 75},
    ]

    budget = 95
    min_reach = 650
    risk_penalty = 0.6

    channel_caps = {
        "Social": 2,
        "Search": 2,
        "Email": 2,
        "TV": 1,
    }

    return {
        "campaigns": campaigns,
        "budget": budget,
        "min_reach": min_reach,
        "risk_penalty": risk_penalty,
        "channel_caps": channel_caps,
    }
