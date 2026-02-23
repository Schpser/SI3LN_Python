/*
 * SI3LN C++ API Client Example
 * Demonstrates how to integrate the Django API with C++ game
 * 
 * Requirements: libcurl, nlohmann/json
 * Compile: g++ -std=c++17 api_client_example.cpp -lcurl -o api_client
 */

#include <iostream>
#include <string>
#include <curl/curl.h>
#include <memory>

class SI3LNAPIClient {
private:
    std::string baseUrl;
    std::string token;
    int playerId;
    
    // Callback for curl response
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
        userp->append((char*)contents, size * nmemb);
        return size * nmemb;
    }
    
    // Make HTTP request
    std::string makeRequest(const std::string& url, const std::string& method, 
                           const std::string& data = "", bool useAuth = false) {
        CURL* curl = curl_easy_init();
        std::string response;
        
        if (curl) {
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
            
            struct curl_slist* headers = nullptr;
            headers = curl_slist_append(headers, "Content-Type: application/json");
            
            if (useAuth && !token.empty()) {
                std::string authHeader = "Authorization: Bearer " + token;
                headers = curl_slist_append(headers, authHeader.c_str());
            }
            
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            
            if (method == "POST") {
                curl_easy_setopt(curl, CURLOPT_POST, 1L);
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
            } else if (method == "PUT") {
                curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
            }
            
            CURLcode res = curl_easy_perform(curl);
            
            if (res != CURLE_OK) {
                std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
            }
            
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
        }
        
        return response;
    }

public:
    SI3LNAPIClient(const std::string& url = "http://localhost:8000/api") 
        : baseUrl(url), playerId(0) {}
    
    // Register new player
    bool registerPlayer(const std::string& username, const std::string& password) {
        std::string url = baseUrl + "/auth/register";
        std::string data = R"({"username":")" + username + R"(","password":")" + password + R"("})";
        
        std::string response = makeRequest(url, "POST", data);
        
        // Parse response (simplified - use proper JSON parser in production)
        if (response.find("token") != std::string::npos) {
            std::cout << "✅ Player registered successfully!" << std::endl;
            // Extract token and player_id from response (use JSON parser)
            return true;
        }
        
        std::cerr << "❌ Registration failed" << std::endl;
        return false;
    }
    
    // Login player
    bool login(const std::string& username, const std::string& password) {
        std::string url = baseUrl + "/auth/login";
        std::string data = R"({"username":")" + username + R"(","password":")" + password + R"("})";
        
        std::string response = makeRequest(url, "POST", data);
        
        if (response.find("token") != std::string::npos) {
            std::cout << "✅ Login successful!" << std::endl;
            // Parse and store token, player_id
            return true;
        }
        
        std::cerr << "❌ Login failed" << std::endl;
        return false;
    }
    
    // Start game session
    int startGameSession(int worldId = 1) {
        std::string url = baseUrl + "/game/sessions/start?player_id=" + std::to_string(playerId);
        std::string data = R"({"world_id":)" + std::to_string(worldId) + R"(,"level_reached":1})";
        
        std::string response = makeRequest(url, "POST", data, true);
        
        if (response.find("id") != std::string::npos) {
            std::cout << "🎮 Game session started!" << std::endl;
            // Parse and return session ID
            return 1; // Return actual session ID from parsed response
        }
        
        return -1;
    }
    
    // Update game session
    bool updateGameSession(int sessionId, int score, int level, int enemies, 
                          int bullets, int duration, bool completed = false) {
        std::string url = baseUrl + "/game/sessions/" + std::to_string(sessionId);
        
        std::string data = R"({)";
        data += R"("score":)" + std::to_string(score) + ",";
        data += R"("level_reached":)" + std::to_string(level) + ",";
        data += R"("enemies_killed":)" + std::to_string(enemies) + ",";
        data += R"("bullets_fired":)" + std::to_string(bullets) + ",";
        data += R"("duration_seconds":)" + std::to_string(duration) + ",";
        data += R"("completed":)" + (completed ? "true" : "false");
        data += "}";
        
        std::string response = makeRequest(url, "PUT", data, true);
        
        if (response.find("score") != std::string::npos) {
            std::cout << "📊 Session updated - Score: " << score << std::endl;
            return true;
        }
        
        return false;
    }
    
    // Get leaderboard
    void getLeaderboard(const std::string& period = "ALL_TIME") {
        std::string url = baseUrl + "/game/leaderboard/" + period;
        std::string response = makeRequest(url, "GET");
        
        std::cout << "\n🏆 Leaderboard (" << period << ")" << std::endl;
        std::cout << response << std::endl; // Parse and display properly
    }
};


// Example game integration
class GameWithAPI {
private:
    SI3LNAPIClient apiClient;
    int currentSessionId;
    int currentScore;
    int currentLevel;
    int enemiesKilled;
    int bulletsFired;
    int gameStartTime;
    
public:
    GameWithAPI() : currentSessionId(-1), currentScore(0), currentLevel(1),
                    enemiesKilled(0), bulletsFired(0), gameStartTime(0) {}
    
    void startGame() {
        std::cout << "🎮 Starting Game..." << std::endl;
        
        // Login player
        apiClient.login("player1", "password123");
        
        // Start session
        currentSessionId = apiClient.startGameSession(1);
        gameStartTime = time(nullptr);
        
        std::cout << "Game started! Session ID: " << currentSessionId << std::endl;
    }
    
    void onEnemyKilled() {
        enemiesKilled++;
        currentScore += 10;
        std::cout << "Enemy killed! Score: " << currentScore << std::endl;
    }
    
    void onBulletFired() {
        bulletsFired++;
    }
    
    void onLevelComplete() {
        currentLevel++;
        std::cout << "Level " << currentLevel << " reached!" << std::endl;
    }
    
    void endGame() {
        int duration = time(nullptr) - gameStartTime;
        
        std::cout << "\n📊 Game Over!" << std::endl;
        std::cout << "Final Score: " << currentScore << std::endl;
        std::cout << "Level: " << currentLevel << std::endl;
        std::cout << "Enemies Killed: " << enemiesKilled << std::endl;
        
        // Update session with final stats
        apiClient.updateGameSession(
            currentSessionId,
            currentScore,
            currentLevel,
            enemiesKilled,
            bulletsFired,
            duration,
            true // completed
        );
        
        // Get leaderboard
        apiClient.getLeaderboard();
    }
};


int main() {
    std::cout << "================================" << std::endl;
    std::cout << "  SI3LN C++ API Client Example  " << std::endl;
    std::cout << "================================" << std::endl;
    
    GameWithAPI game;
    
    // Simulate game
    game.startGame();
    
    // Simulate gameplay
    for (int i = 0; i < 10; i++) {
        game.onBulletFired();
        if (i % 2 == 0) {
            game.onEnemyKilled();
        }
    }
    
    game.onLevelComplete();
    game.endGame();
    
    std::cout << "\n✨ Example complete!" << std::endl;
    
    return 0;
}
