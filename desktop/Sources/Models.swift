// Copyright 2026 Scion Frontiers & Antigravity
// Data Models for Harness-Suprem Native macOS Desktop App

import Foundation

public enum InferenceEngine: String, CaseIterable, Identifiable {
    case mlx = "Apple MLX (Metal)"
    case llamaCpp = "llama.cpp (Metal GGUF)"
    
    public var id: String { rawValue }
    
    public var port: Int {
        switch self {
        case .mlx: return 5248
        case .llamaCpp: return 5249
        }
    }
    
    public var defaultModel: String {
        switch self {
        case .mlx: return "Qwen3.6-35B-A3B-8bit"
        case .llamaCpp: return "Gemma-4-26B-Instruct (GGUF)"
        }
    }
    
    public var memoryAllocatedGB: Double {
        switch self {
        case .mlx: return 36.9
        case .llamaCpp: return 15.8
        }
    }
}

public struct ChatMessage: Identifiable, Equatable {
    public let id: UUID
    public var role: String // "user", "assistant", "system"
    public var content: String
    public var timestamp: Date
    public var isStreaming: Bool
    public var tokensGenerated: Int
    
    public init(id: UUID = UUID(), role: String, content: String, timestamp: Date = Date(), isStreaming: Bool = false, tokensGenerated: Int = 0) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.isStreaming = isStreaming
        self.tokensGenerated = tokensGenerated
    }
}

public struct PluginItem: Identifiable, Equatable {
    public let id: String
    public let name: String
    public let category: String
    public var isEnabled: Bool
    public let description: String
    
    public init(id: String, name: String, category: String, isEnabled: Bool = true, description: String) {
        self.id = id
        self.name = name
        self.category = category
        self.isEnabled = isEnabled
        self.description = description
    }
}

public struct EngineStatus: Equatable {
    public var isOnline: Bool
    public var port: Int
    public var modelName: String
    public var memoryAllocatedGB: Double
    public var tokensPerSec: Double
    public var activeEngine: InferenceEngine
    
    public static let initial = EngineStatus(
        isOnline: false,
        port: 5248,
        modelName: "Qwen3.6-35B-A3B-8bit (MLX Native)",
        memoryAllocatedGB: 36.9,
        tokensPerSec: 0.0,
        activeEngine: .mlx
    )
}
