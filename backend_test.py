#!/usr/bin/env python3
"""
Comprehensive Backend Testing for SuperBetter-inspired Gamified Personal Growth App
Tests all backend APIs including authentication, quests, power-ups, bad guys, XP system, etc.
"""

import requests
import json
import time
from datetime import datetime, timezone
import uuid

# Backend URL from frontend .env
BASE_URL = "https://levelup-daily.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"Content-Type": "application/json"}
        
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=default_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def test_user_registration(self):
        """Test user registration with valid data"""
        test_name = "User Registration"
        
        # Generate unique user data
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"sarah.johnson.{unique_id}@example.com",
            "username": f"sarah_j_{unique_id}",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        
        if response is None:
            self.log_result(test_name, False, "Network error during registration")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                self.auth_token = data["token"]
                self.user_id = data["user"]["id"]
                self.log_result(test_name, True, "User registered successfully", 
                              f"User ID: {self.user_id}, Username: {data['user']['username']}")
                return True
            else:
                self.log_result(test_name, False, "Missing token or user data in response")
                return False
        else:
            self.log_result(test_name, False, f"Registration failed with status {response.status_code}", 
                          response.text)
            return False
    
    def test_user_login(self):
        """Test user login with correct credentials"""
        test_name = "User Login"
        
        # First register a user for login test
        unique_id = str(uuid.uuid4())[:8]
        register_data = {
            "email": f"mike.wilson.{unique_id}@example.com",
            "username": f"mike_w_{unique_id}",
            "password": "LoginTest456!"
        }
        
        # Register user
        register_response = self.make_request("POST", "/auth/register", register_data)
        if not register_response or register_response.status_code != 200:
            self.log_result(test_name, False, "Failed to register user for login test")
            return False
        
        # Now test login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response is None:
            self.log_result(test_name, False, "Network error during login")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                self.log_result(test_name, True, "User login successful", 
                              f"Token received, User: {data['user']['username']}")
                return True
            else:
                self.log_result(test_name, False, "Missing token or user data in login response")
                return False
        else:
            self.log_result(test_name, False, f"Login failed with status {response.status_code}", 
                          response.text)
            return False
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        test_name = "Invalid Login Handling"
        
        invalid_login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_login_data)
        
        if response is None:
            self.log_result(test_name, False, "Network error during invalid login test")
            return False
        
        if response.status_code == 401:
            self.log_result(test_name, True, "Invalid login correctly rejected with 401")
            return True
        else:
            self.log_result(test_name, False, f"Expected 401 for invalid login, got {response.status_code}")
            return False
    
    def test_quest_creation(self):
        """Test creating quests of all types"""
        test_name = "Quest Creation"
        
        if not self.auth_token:
            self.log_result(test_name, False, "No auth token available")
            return False
        
        quest_types = [
            {"type": "Daily", "expected_xp": 10, "title": "Morning Meditation", "description": "10 minutes of mindful meditation"},
            {"type": "Weekly", "expected_xp": 25, "title": "Weekly Workout Plan", "description": "Complete 3 gym sessions this week"},
            {"type": "Epic", "expected_xp": 50, "title": "Learn New Skill", "description": "Complete online course in Python programming"}
        ]
        
        created_quests = []
        
        for quest_info in quest_types:
            quest_data = {
                "title": quest_info["title"],
                "description": quest_info["description"],
                "quest_type": quest_info["type"]
            }
            
            response = self.make_request("POST", "/quests", quest_data)
            
            if response is None:
                self.log_result(test_name, False, f"Network error creating {quest_info['type']} quest")
                return False
            
            if response.status_code == 200:
                quest = response.json()
                if quest["xp_reward"] == quest_info["expected_xp"]:
                    created_quests.append(quest)
                else:
                    self.log_result(test_name, False, 
                                  f"{quest_info['type']} quest XP mismatch: expected {quest_info['expected_xp']}, got {quest['xp_reward']}")
                    return False
            else:
                self.log_result(test_name, False, 
                              f"Failed to create {quest_info['type']} quest: {response.status_code}")
                return False
        
        self.log_result(test_name, True, f"Successfully created {len(created_quests)} quests", 
                      f"Daily: 10 XP, Weekly: 25 XP, Epic: 50 XP")
        return created_quests
    
    def test_quest_completion(self):
        """Test quest completion and XP award"""
        test_name = "Quest Completion & XP Award"
        
        # First create a quest
        quest_data = {
            "title": "Read 20 Pages",
            "description": "Read 20 pages of personal development book",
            "quest_type": "Daily"
        }
        
        create_response = self.make_request("POST", "/quests", quest_data)
        if not create_response or create_response.status_code != 200:
            self.log_result(test_name, False, "Failed to create quest for completion test")
            return False
        
        quest = create_response.json()
        quest_id = quest["id"]
        
        # Complete the quest
        complete_response = self.make_request("PUT", f"/quests/{quest_id}/complete")
        
        if complete_response is None:
            self.log_result(test_name, False, "Network error during quest completion")
            return False
        
        if complete_response.status_code == 200:
            completion_data = complete_response.json()
            if "xp_gained" in completion_data and completion_data["xp_gained"] == 10:
                self.log_result(test_name, True, "Quest completed successfully", 
                              f"XP gained: {completion_data['xp_gained']}")
                return True
            else:
                self.log_result(test_name, False, "Quest completion response missing XP data")
                return False
        else:
            self.log_result(test_name, False, f"Quest completion failed: {complete_response.status_code}")
            return False
    
    def test_power_up_system(self):
        """Test power-up creation and logging"""
        test_name = "Power-Up System"
        
        # Create a power-up
        power_up_data = {
            "title": "Energizing Green Tea",
            "description": "Drink green tea for natural energy boost"
        }
        
        create_response = self.make_request("POST", "/power-ups", power_up_data)
        
        if not create_response or create_response.status_code != 200:
            self.log_result(test_name, False, "Failed to create power-up")
            return False
        
        power_up = create_response.json()
        power_up_id = power_up["id"]
        
        # Log power-up usage
        log_response = self.make_request("POST", f"/power-ups/{power_up_id}/log")
        
        if log_response is None:
            self.log_result(test_name, False, "Network error during power-up logging")
            return False
        
        if log_response.status_code == 200:
            log_data = log_response.json()
            if "xp_gained" in log_data and log_data["xp_gained"] == 5:
                self.log_result(test_name, True, "Power-up system working correctly", 
                              f"Created and logged power-up, XP gained: {log_data['xp_gained']}")
                return True
            else:
                self.log_result(test_name, False, "Power-up logging response missing XP data")
                return False
        else:
            self.log_result(test_name, False, f"Power-up logging failed: {log_response.status_code}")
            return False
    
    def test_bad_guy_system(self):
        """Test bad guy creation and defeat mechanics"""
        test_name = "Bad Guy System"
        
        # Create a bad guy
        bad_guy_data = {
            "title": "Procrastination Monster",
            "description": "The evil force that prevents productivity",
            "max_hp": 100
        }
        
        create_response = self.make_request("POST", "/bad-guys", bad_guy_data)
        
        if not create_response or create_response.status_code != 200:
            self.log_result(test_name, False, "Failed to create bad guy")
            return False
        
        bad_guy = create_response.json()
        bad_guy_id = bad_guy["id"]
        
        # Test defeat mechanics (deal damage)
        defeat_response = self.make_request("POST", f"/bad-guys/{bad_guy_id}/defeat", {"damage": 25})
        
        if defeat_response is None:
            self.log_result(test_name, False, "Network error during bad guy defeat")
            return False
        
        if defeat_response.status_code == 200:
            defeat_data = defeat_response.json()
            if "xp_gained" in defeat_data and defeat_data["xp_gained"] == 15:
                self.log_result(test_name, True, "Bad guy system working correctly", 
                              f"Created bad guy and dealt damage, XP gained: {defeat_data['xp_gained']}")
                return True
            else:
                self.log_result(test_name, False, "Bad guy defeat response missing XP data")
                return False
        else:
            self.log_result(test_name, False, f"Bad guy defeat failed: {defeat_response.status_code}")
            return False
    
    def test_dashboard_api(self):
        """Test dashboard statistics API"""
        test_name = "Dashboard Statistics API"
        
        if not self.auth_token:
            self.log_result(test_name, False, "No auth token available")
            return False
        
        response = self.make_request("GET", "/dashboard")
        
        if response is None:
            self.log_result(test_name, False, "Network error accessing dashboard")
            return False
        
        if response.status_code == 200:
            dashboard_data = response.json()
            required_fields = ["user", "quests_today", "quests_completed_today"]
            
            missing_fields = [field for field in required_fields if field not in dashboard_data]
            
            if not missing_fields:
                self.log_result(test_name, True, "Dashboard API working correctly", 
                              f"User level: {dashboard_data['user']['level']}, XP: {dashboard_data['user']['total_xp']}")
                return True
            else:
                self.log_result(test_name, False, f"Dashboard missing fields: {missing_fields}")
                return False
        else:
            self.log_result(test_name, False, f"Dashboard API failed: {response.status_code}")
            return False
    
    def test_side_quest_system(self):
        """Test side quest system"""
        test_name = "Side Quest System"
        
        # Get daily side quest
        response = self.make_request("GET", "/side-quests/daily")
        
        if response is None:
            self.log_result(test_name, False, "Network error getting daily side quest")
            return False
        
        if response.status_code == 200:
            side_quest = response.json()
            if side_quest and "title" in side_quest and "xp_reward" in side_quest:
                # Test completing side quest
                if self.auth_token:
                    complete_response = self.make_request("POST", "/side-quests/complete")
                    if complete_response and complete_response.status_code == 200:
                        complete_data = complete_response.json()
                        if "xp_gained" in complete_data:
                            self.log_result(test_name, True, "Side quest system working correctly", 
                                          f"Retrieved and completed side quest: {side_quest['title']}, XP: {complete_data['xp_gained']}")
                            return True
                
                self.log_result(test_name, True, "Side quest retrieval working", 
                              f"Retrieved side quest: {side_quest['title']}")
                return True
            else:
                self.log_result(test_name, False, "Side quest response missing required fields")
                return False
        else:
            self.log_result(test_name, False, f"Side quest API failed: {response.status_code}")
            return False
    
    def test_xp_and_leveling(self):
        """Test XP accumulation and level calculation"""
        test_name = "XP and Leveling System"
        
        if not self.auth_token:
            self.log_result(test_name, False, "No auth token available")
            return False
        
        # Get initial dashboard to check current XP/level
        initial_response = self.make_request("GET", "/dashboard")
        if not initial_response or initial_response.status_code != 200:
            self.log_result(test_name, False, "Failed to get initial user stats")
            return False
        
        initial_data = initial_response.json()
        initial_xp = initial_data["user"]["total_xp"]
        initial_level = initial_data["user"]["level"]
        
        # Create and complete multiple quests to gain XP
        for i in range(3):
            quest_data = {
                "title": f"XP Test Quest {i+1}",
                "description": f"Test quest for XP accumulation {i+1}",
                "quest_type": "Daily"
            }
            
            create_response = self.make_request("POST", "/quests", quest_data)
            if create_response and create_response.status_code == 200:
                quest = create_response.json()
                complete_response = self.make_request("PUT", f"/quests/{quest['id']}/complete")
                if not complete_response or complete_response.status_code != 200:
                    self.log_result(test_name, False, f"Failed to complete test quest {i+1}")
                    return False
        
        # Check final XP/level
        final_response = self.make_request("GET", "/dashboard")
        if not final_response or final_response.status_code != 200:
            self.log_result(test_name, False, "Failed to get final user stats")
            return False
        
        final_data = final_response.json()
        final_xp = final_data["user"]["total_xp"]
        final_level = final_data["user"]["level"]
        
        xp_gained = final_xp - initial_xp
        expected_level = max(1, final_xp // 100)
        
        if xp_gained >= 30 and final_level == expected_level:  # 3 daily quests = 30 XP
            self.log_result(test_name, True, "XP and leveling system working correctly", 
                          f"XP: {initial_xp} → {final_xp} (+{xp_gained}), Level: {initial_level} → {final_level}")
            return True
        else:
            self.log_result(test_name, False, 
                          f"XP/Level calculation error. XP gained: {xp_gained}, Level: {final_level}, Expected: {expected_level}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Comprehensive Backend Testing for SuperBetter-inspired App")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_user_registration():
            print("❌ Registration failed - cannot continue with authenticated tests")
            return
        
        self.test_user_login()
        self.test_invalid_login()
        
        # Test core game mechanics
        self.test_quest_creation()
        self.test_quest_completion()
        self.test_power_up_system()
        self.test_bad_guy_system()
        self.test_xp_and_leveling()
        self.test_side_quest_system()
        self.test_dashboard_api()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()