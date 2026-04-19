#!/usr/bin/env python3
"""
Data seeding script for MoodMate.

Creates sample users with tasks and populates the hacks knowledge base for quick
testing. Assumes the FastAPI backend is running locally on port 8000.
"""

import json
from datetime import datetime, timedelta

import requests

BASE_URL = "http://localhost:8000"


def create_user_and_get_token(username: str, password: str):
    """Create a user and return the auth token."""
    response = requests.post(
        f"{BASE_URL}/user/init",
        json={"username": username, "password": password},
    )
    if response.status_code == 200:
        data = response.json()
        return data["data"]["token"]
    print(f"[user] Failed to create {username}: {response.text}")
    return None


def create_task(token: str, title: str, description: str, priority: str, deadline=None):
    """Create a task for the authenticated user."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": title,
        "description": description,
        "priority": priority,
    }
    if deadline:
        data["deadline"] = deadline

    response = requests.post(f"{BASE_URL}/tasks/", json=data, headers=headers)
    if response.status_code == 200:
        print(f"[task] Created: {title}")
        return True
    print(f"[task] Failed: {title} -> {response.text}")
    return False


def create_hack(token: str, title: str, content: str, category=None, tags=None):
    """Create a hack/article for the knowledge base."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": title,
        "content": content,
        "category": category,
        "tags": tags or [],
    }
    response = requests.post(f"{BASE_URL}/hacks/", json=data, headers=headers)
    if response.status_code == 200:
        print(f"[hack] Created: {title}")
        return True
    print(f"[hack] Failed: {title} -> {response.text}")
    return False


def main():
    print("Seeding MoodMate sample data...")

    users_data = [
        {
            "username": "alice@example.com",
            "password": "password123",
            "tasks": [
                {
                    "title": "Complete project proposal",
                    "description": "Write and submit the final project proposal for CMPS 279",
                    "priority": "HIGH",
                    "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
                },
                {
                    "title": "Study for midterm",
                    "description": "Review all course materials and practice problems",
                    "priority": "URGENT",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                },
                {
                    "title": "Grocery shopping",
                    "description": "Buy ingredients for the week",
                    "priority": "LOW",
                    "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
                },
            ],
        },
        {
            "username": "bob@example.com",
            "password": "password123",
            "tasks": [
                {
                    "title": "Fix bug in authentication",
                    "description": "Debug the login issue reported by users",
                    "priority": "HIGH",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                },
                {
                    "title": "Update documentation",
                    "description": "Add API documentation for new endpoints",
                    "priority": "MEDIUM",
                    "deadline": (datetime.now() + timedelta(days=5)).isoformat(),
                },
                {
                    "title": "Team meeting",
                    "description": "Weekly standup with development team",
                    "priority": "LOW",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                },
            ],
        },
        {
            "username": "charlie@example.com",
            "password": "password123",
            "tasks": [
                {
                    "title": "Design user interface",
                    "description": "Create mockups for the mobile app interface",
                    "priority": "MEDIUM",
                    "deadline": (datetime.now() + timedelta(days=4)).isoformat(),
                },
                {
                    "title": "Code review",
                    "description": "Review pull requests from team members",
                    "priority": "HIGH",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                },
            ],
        },
    ]

    sample_hacks = [
        {
            "title": "2-Minute Reset for Overwhelm",
            "content": "Stand up, take 10 slow breaths, and name one small win from today. This interrupts the stress loop and clears your head before the next task.",
            "category": "wellness",
            "tags": ["anxiety", "breathing", "reset"],
        },
        {
            "title": "The 25/5 Focus Sprint",
            "content": "Work for 25 minutes with all notifications off, then take a 5-minute break. Stack three sprints to finish one meaningful chunk.",
            "category": "productivity",
            "tags": ["focus", "pomodoro", "deep work"],
        },
        {
            "title": "Write the First Messy Draft",
            "content": "When stuck, commit to writing the worst version in 10 minutes. Momentum beats perfection; you can edit after you see it on the page.",
            "category": "creativity",
            "tags": ["writer's block", "procrastination"],
        },
        {
            "title": "Micro-Plan Tomorrow Tonight",
            "content": "Before bed, pick your single most important task and the first 2 steps. Your morning brain follows a clear script instead of negotiating.",
            "category": "planning",
            "tags": ["morning routine", "priorities"],
        },
        {
            "title": "Calm Body, Calm Mind",
            "content": "Relax your jaw, drop your shoulders, and unclench your hands. Physical tension fuels anxious thoughts; releasing it gives you more control.",
            "category": "wellness",
            "tags": ["grounding", "stress"],
        },
    ]

    first_user_token = None
    for idx, user_data in enumerate(users_data):
        print(f"\nCreating user: {user_data['username']}")
        token = create_user_and_get_token(user_data["username"], user_data["password"])
        if idx == 0 and token:
            first_user_token = token

        if token:
            print(f"Adding {len(user_data['tasks'])} tasks...")
            for task in user_data["tasks"]:
                create_task(token, **task)
        else:
            print(f"Skipping tasks for {user_data['username']} (no token)")

    if first_user_token:
        print(f"\nAdding {len(sample_hacks)} hacks...")
        for hack in sample_hacks:
            create_hack(first_user_token, **hack)
    else:
        print("No valid token available; skipping hack creation.")

    print("\nSeeding complete! Test with:")
    for user_data in users_data:
        print(f"  - {user_data['username']} / {user_data['password']}")


if __name__ == "__main__":
    main()
