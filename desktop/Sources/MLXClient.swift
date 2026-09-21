// Copyright 2026 Scion Frontiers & Antigravity
// Native Swift Dual-Engine Client (Apple MLX Metal + llama.cpp Metal GGUF)

import Foundation
import Combine

@MainActor
public class MLXClient: ObservableObject {
    @Published public var engineStatus: EngineStatus = .initial
    @Published public var activeEngine: InferenceEngine = .mlx {
        didSet {
            engineStatus.activeEngine = activeEngine
            engineStatus.port = activeEngine.port
            engineStatus.modelName = activeEngine.defaultModel
            engineStatus.memoryAllocatedGB = activeEngine.memoryAllocatedGB
            checkHealth()
        }
    }
    @Published public var isGenerating: Bool = false
    
    private let host = "127.0.0.1"
    private var currentTask: Task<Void, Never>? = nil
    
    public init() {
        checkHealth()
    }
    
    public func checkHealth() {
        let currentPort = activeEngine.port
        let healthPath = (activeEngine == .mlx) ? "/v1/models" : "/health"
        Task {
            let url = URL(string: "http://\(self.host):\(currentPort)\(healthPath)")!
            var req = URLRequest(url: url)
            req.timeoutInterval = 1.0
            do {
                let (_, response) = try await URLSession.shared.data(for: req)
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    self.engineStatus.isOnline = true
                } else {
                    self.engineStatus.isOnline = false
                }
            } catch {
                self.engineStatus.isOnline = false
            }
        }
    }
    
    public func ensureEngineRunning() async {
        if engineStatus.isOnline { return }
        
        let basePath = "/Users/rarescristea/Desktop/harness-suprem"
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        
        if activeEngine == .mlx {
            let bridgePath = "\(basePath)/desktop/engine/mlx_bridge.py"
            proc.arguments = [bridgePath, "--start", "--port", "\(activeEngine.port)"]
        } else {
            let llamaBridgePath = "\(basePath)/core/engine/llama_bridge.py"
            proc.arguments = [llamaBridgePath, "--start"]
        }
        
        try? proc.run()
        
        // Poll for up to 15 seconds
        for _ in 0..<15 {
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            checkHealth()
            if engineStatus.isOnline { break }
        }
    }
    
    public func streamCompletion(
        messages: [ChatMessage],
        systemPrompt: String = "You are the Supreme Coding Agent powered by Apple Silicon.",
        onToken: @escaping (String) -> Void,
        onComplete: @escaping (Int, Double) -> Void
    ) {
        guard !isGenerating else { return }
        isGenerating = true
        
        let targetPort = activeEngine.port
        let engineName = activeEngine.rawValue
        
        currentTask = Task {
            let url = URL(string: "http://\(self.host):\(targetPort)/v1/chat/completions")!
            var req = URLRequest(url: url)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.setValue("Bearer dual-native", forHTTPHeaderField: "Authorization")
            
            var payloadMessages: [[String: String]] = [
                ["role": "system", "content": systemPrompt]
            ]
            for m in messages {
                payloadMessages.append(["role": m.role, "content": m.content])
            }
            
            let body: [String: Any] = [
                "model": "default_model",
                "messages": payloadMessages,
                "stream": true,
                "max_tokens": 8192,
                "temperature": 0.2
            ]
            
            req.httpBody = try? JSONSerialization.data(withJSONObject: body)
            
            let startTime = CFAbsoluteTimeGetCurrent()
            var tokenCount = 0
            
            do {
                let (bytes, response) = try await URLSession.shared.bytes(for: req)
                guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                    onToken("\n[\(engineName) Connection Error: HTTP response not OK. Please verify engine is running on port \(targetPort).]")
                    self.isGenerating = false
                    return
                }
                
                self.engineStatus.isOnline = true
                
                for try await line in bytes.lines {
                    let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                    if trimmed.isEmpty || trimmed == "data: [DONE]" { continue }
                    if trimmed.hasPrefix("data: ") {
                        let jsonStr = String(trimmed.dropFirst(6))
                        if let data = jsonStr.data(using: .utf8),
                           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                           let choices = json["choices"] as? [[String: Any]],
                           let first = choices.first,
                           let delta = first["delta"] as? [String: Any],
                           let content = delta["content"] as? String {
                            tokenCount += 1
                            onToken(content)
                            
                            // Update speed
                            let elapsed = CFAbsoluteTimeGetCurrent() - startTime
                            if elapsed > 0 {
                                self.engineStatus.tokensPerSec = round((Double(tokenCount) / elapsed) * 10.0) / 10.0
                            }
                        }
                    }
                }
            } catch {
                if !Task.isCancelled {
                    onToken("\n[\(engineName) Streaming error: \(error.localizedDescription)]")
                }
            }
            
            let totalElapsed = CFAbsoluteTimeGetCurrent() - startTime
            let finalTps = totalElapsed > 0 ? Double(tokenCount) / totalElapsed : 0.0
            self.isGenerating = false
            onComplete(tokenCount, finalTps)
        }
    }
    
    public func stopGeneration() {
        currentTask?.cancel()
        currentTask = nil
        isGenerating = false
    }
}
