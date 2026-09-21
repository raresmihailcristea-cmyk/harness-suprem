// Copyright 2026 Scion Frontiers & Antigravity
// Native MemPalace Service for Harness-Suprem Desktop App

import Foundation
import Combine

public struct MemPalaceStatus {
    public var isAvailable: Bool = false
    public var totalDrawers: Int = 0
    public var entitiesCount: Int = 0
    public var triplesCount: Int = 0
    public var diaryEntries: Int = 0
    public var wakeUpSnippet: String = ""
    
    public init(isAvailable: Bool = false, totalDrawers: Int = 0, entitiesCount: Int = 0, triplesCount: Int = 0, diaryEntries: Int = 0, wakeUpSnippet: String = "") {
        self.isAvailable = isAvailable
        self.totalDrawers = totalDrawers
        self.entitiesCount = entitiesCount
        self.triplesCount = triplesCount
        self.diaryEntries = diaryEntries
        self.wakeUpSnippet = wakeUpSnippet
    }
}

@MainActor
public class MemPalaceService: ObservableObject {
    @Published public var status: MemPalaceStatus = MemPalaceStatus()
    @Published public var isPalaceActive: Bool = true
    
    public init() {
        refresh()
    }
    
    public func refresh() {
        Task.detached {
            let s = self.fetchStatusFromBridge()
            let wake = self.fetchWakeUpContext()
            await MainActor.run {
                var updated = s
                updated.wakeUpSnippet = wake
                self.status = updated
            }
        }
    }
    
    private nonisolated func fetchStatusFromBridge() -> MemPalaceStatus {
        let task = Process()
        let pipe = Pipe()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        task.currentDirectoryURL = URL(fileURLWithPath: "/Users/rarescristea/Desktop/harness-suprem")
        task.arguments = ["-c", "import json; from core.memory.mempalace.palace_bridge import MemPalaceBridge; print(json.dumps(MemPalaceBridge().get_status()))"]
        task.standardOutput = pipe
        task.standardError = Pipe()
        
        do {
            try task.run()
            task.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                return MemPalaceStatus(
                    isAvailable: json["is_available"] as? Bool ?? false,
                    totalDrawers: json["total_drawers"] as? Int ?? 0,
                    entitiesCount: json["entities_count"] as? Int ?? 0,
                    triplesCount: json["triples_count"] as? Int ?? 0,
                    diaryEntries: json["diary_entries"] as? Int ?? 0,
                    wakeUpSnippet: ""
                )
            }
        } catch {
            print("MemPalace status fetch error: \(error)")
        }
        return MemPalaceStatus()
    }
    
    public nonisolated func fetchWakeUpContext() -> String {
        let task = Process()
        let pipe = Pipe()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        task.currentDirectoryURL = URL(fileURLWithPath: "/Users/rarescristea/Desktop/harness-suprem")
        task.arguments = ["-c", "from core.memory.mempalace.palace_bridge import MemPalaceBridge; print(MemPalaceBridge().get_wake_up_context())"]
        task.standardOutput = pipe
        task.standardError = Pipe()
        
        do {
            try task.run()
            task.waitUntilExit()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            return String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        } catch {
            return ""
        }
    }
}
