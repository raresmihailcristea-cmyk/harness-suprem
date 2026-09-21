// Copyright 2026 Scion Frontiers & Antigravity
// Native macOS SwiftUI User Interface for Harness-Suprem Desktop App

import SwiftUI

public struct ContentView: View {
    @StateObject private var client = MLXClient()
    @StateObject private var palace = MemPalaceService()
    @State private var messages: [ChatMessage] = [
        ChatMessage(
            role: "assistant",
            content: "Salut! Sunt **Harness-Suprem**, conectat direct la modelul **Qwen3.6-35B-8bit** prin **Apple MLX (Metal GPU)** pe Apple M1 Ultra (128GB Memorie Unificată).\n\nToate cele **17 plugin-uri de sistem**, inclusiv **MemPalace v3.10** (208 sertare active), porțile de calitate AST și auditorul Apple sunt active. Cu ce proiect începem astăzi?"
        )
    ]
    @State private var inputText: String = ""
    @State private var qualityGateEnabled: Bool = true
    @State private var securityScrubberEnabled: Bool = true
    @State private var tddDisciplineEnabled: Bool = true
    @State private var showingSettings: Bool = false
    
    // 17 Plugins Registry
    @State private var plugins: [PluginItem] = [
        PluginItem(id: "1", name: "apple-developer", category: "Platform", isEnabled: true, description: "Xcode/Swift 6, simctl, HIG & App Store Compliance Gate"),
        PluginItem(id: "2", name: "anthropic", category: "Provider", isEnabled: true, description: "Claude 3.5 Sonnet / Opus runner"),
        PluginItem(id: "3", name: "openai", category: "Provider", isEnabled: true, description: "GPT-4o, o1, and o3 reasoning model"),
        PluginItem(id: "4", name: "xai", category: "Provider", isEnabled: true, description: "xAI Grok reasoning engine"),
        PluginItem(id: "5", name: "nvidia", category: "Provider", isEnabled: true, description: "NVIDIA NIM Cloud (DeepSeek-V3/R1)"),
        PluginItem(id: "6", name: "ollama", category: "Provider", isEnabled: false, description: "Offline local air-gapped runner"),
        PluginItem(id: "7", name: "codex", category: "Execution", isEnabled: true, description: "AST parsing, smart patching & test gen"),
        PluginItem(id: "8", name: "linux-node", category: "Execution", isEnabled: true, description: "Container sandbox supervisor"),
        PluginItem(id: "9", name: "cua-computer", category: "Execution", isEnabled: true, description: "Computer-Use Agent GUI automation"),
        PluginItem(id: "10", name: "browser", category: "Interaction", isEnabled: true, description: "Headless web automation & screenshots"),
        PluginItem(id: "11", name: "canvas", category: "Interaction", isEnabled: true, description: "Generative UI live preview"),
        PluginItem(id: "12", name: "talk-voice", category: "Interaction", isEnabled: true, description: "Bidirectional voice streaming"),
        PluginItem(id: "13", name: "bonjour", category: "System", isEnabled: true, description: "mDNS Zero-conf local swarm discovery"),
        PluginItem(id: "14", name: "device-pair", category: "System", isEnabled: true, description: "Cryptographic device pairing"),
        PluginItem(id: "15", name: "file-transfer", category: "System", isEnabled: true, description: "High-speed encrypted sync"),
        PluginItem(id: "16", name: "geolocation", category: "Context", isEnabled: true, description: "Timezone & localized presets"),
        PluginItem(id: "17", name: "memory-core", category: "Memory", isEnabled: true, description: "Persistent episodic memory (MemPalace)"),
        PluginItem(id: "18", name: "repo-ingest", category: "Execution", isEnabled: true, description: "Prompt-friendly codebase digestion & token budgeting (gitingest)"),
        PluginItem(id: "19", name: "git-mcp", category: "Provider", isEnabled: true, description: "Live GitHub documentation & code fetcher (idosal/git-mcp)"),
        PluginItem(id: "20", name: "ecc-os", category: "System", isEnabled: true, description: "Enterprise Codebase Context & Agent Harness OS (ECC)"),
        PluginItem(id: "21", name: "worktree-fanout", category: "Execution", isEnabled: true, description: "Parallel Git worktree multi-agent fan-out orchestrator (orca)"),
        PluginItem(id: "22", name: "app-monetization-intel", category: "Platform", isEnabled: true, description: "Competitor pricing, StoreKit 2 IAP, subscriptions & grace period"),
    ]
    
    public init() {}
    
    public var body: some View {
        NavigationSplitView {
            // SIDEBAR
            VStack(alignment: .leading, spacing: 14) {
                // Hardware & Engine Header
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Image(systemName: "cpu.fill")
                            .foregroundColor(.orange)
                        Text("Apple M1 Ultra (128 GB)")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    
                    Picker("Motor", selection: $client.activeEngine) {
                        ForEach(InferenceEngine.allCases) { engine in
                            Text(engine == .mlx ? "Apple MLX" : "llama.cpp").tag(engine)
                        }
                    }
                    .pickerStyle(.segmented)
                    .controlSize(.small)
                    
                    Text("Model: \(client.engineStatus.modelName)")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.blue)
                        .lineLimit(1)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 8)
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(8)
                
                // MemPalace Status Header
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Image(systemName: "brain.head.profile")
                            .foregroundColor(.purple)
                        Text("MemPalace v3.10")
                            .font(.system(size: 12, weight: .semibold))
                        Spacer()
                        Text("\(palace.status.totalDrawers) sertare")
                            .font(.system(size: 10, weight: .bold))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.purple.opacity(0.15))
                            .foregroundColor(.purple)
                            .cornerRadius(4)
                    }
                    HStack(spacing: 6) {
                        Text("KG: \(palace.status.entitiesCount) entități")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                        Text("•")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                        Text("Jurnal: \(palace.status.diaryEntries)")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                    }
                    Toggle("🧠 L0/L1 Context Infiltration", isOn: $palace.isPalaceActive)
                        .font(.system(size: 11))
                        .padding(.top, 2)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(8)
                
                Divider()
                
                // Guardrails & Gates
                VStack(alignment: .leading, spacing: 8) {
                    Text("GUVERNANȚĂ & PORȚI")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.secondary)
                    
                    Toggle("🛡️ LoopGate (AST Mutation)", isOn: $qualityGateEnabled)
                        .font(.system(size: 12))
                    Toggle("🔒 AutoHarness Scrubber", isOn: $securityScrubberEnabled)
                        .font(.system(size: 12))
                    Toggle("🧪 TDD-First Discipline", isOn: $tddDisciplineEnabled)
                        .font(.system(size: 12))
                }
                
                Divider()
                
                // 17 System Plugins List
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("17 SYSTEM PLUGINS")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("\(plugins.filter { $0.isEnabled }.count)/17")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.accentColor)
                    }
                    
                    ScrollView {
                        VStack(spacing: 4) {
                            ForEach($plugins) { $plugin in
                                HStack(spacing: 8) {
                                    Toggle("", isOn: $plugin.isEnabled)
                                        .labelsHidden()
                                        .controlSize(.mini)
                                    VStack(alignment: .leading, spacing: 1) {
                                        Text(plugin.name)
                                            .font(.system(size: 11, weight: .medium))
                                        Text(plugin.category)
                                            .font(.system(size: 9))
                                            .foregroundColor(.secondary)
                                    }
                                    Spacer()
                                }
                                .padding(.vertical, 2)
                            }
                        }
                    }
                }
                
                Spacer()
                
                // Server Connect Button if offline
                if !client.engineStatus.isOnline {
                    Button(action: {
                        Task { await client.ensureEngineRunning() }
                    }) {
                        HStack {
                            Image(systemName: "bolt.fill")
                            Text("Pornește Motorul MLX")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.green)
                }
            }
            .padding(12)
            .navigationSplitViewColumnWidth(min: 240, ideal: 270, max: 320)
        } detail: {
            // MAIN CHAT AREA
            VStack(spacing: 0) {
                // Top HUD Bar
                HStack(spacing: 16) {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(client.engineStatus.isOnline ? Color.green : Color.red)
                            .frame(width: 8, height: 8)
                        Text(client.engineStatus.isOnline ? "\(client.activeEngine == .mlx ? "MLX" : "llama.cpp") Online (Port \(client.engineStatus.port))" : "\(client.activeEngine == .mlx ? "MLX" : "llama.cpp") Deconectat")
                            .font(.system(size: 12, weight: .medium))
                    }
                    
                    Spacer()
                    
                    // Hardware & Memory stats
                    HStack(spacing: 12) {
                        HStack(spacing: 4) {
                            Image(systemName: "brain.head.profile")
                                .foregroundColor(.purple)
                            Text("MemPalace: \(palace.status.totalDrawers) sertare")
                                .font(.system(size: 11, weight: .medium))
                        }
                        
                        HStack(spacing: 4) {
                            Image(systemName: "memorychip")
                                .foregroundColor(.purple)
                            Text("VRAM: ~\(String(format: "%.1f", client.engineStatus.memoryAllocatedGB)) GB / 128 GB")
                                .font(.system(size: 11, weight: .regular))
                        }
                        
                        HStack(spacing: 4) {
                            Image(systemName: "speedometer")
                                .foregroundColor(.blue)
                            Text(String(format: "%.1f tok/s", client.engineStatus.tokensPerSec))
                                .font(.system(size: 11, weight: .semibold))
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(6)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color(NSColor.windowBackgroundColor))
                
                Divider()
                
                // Messages ScrollView
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(messages) { msg in
                                MessageBubble(message: msg)
                            }
                        }
                        .padding(16)
                    }
                    .onChange(of: messages.count) { _, _ in
                        if let last = messages.last {
                            withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                        }
                    }
                    .onChange(of: messages.last?.content) { _, _ in
                        if let last = messages.last {
                            proxy.scrollTo(last.id, anchor: .bottom)
                        }
                    }
                }
                
                Divider()
                
                // Quick Action Bar
                HStack(spacing: 8) {
                    QuickActionButton(title: client.activeEngine == .mlx ? "🦙 Comută pe llama.cpp" : "⚡ Comută pe Apple MLX", action: {
                        client.activeEngine = (client.activeEngine == .mlx) ? .llamaCpp : .mlx
                    })
                    QuickActionButton(title: "🧠 MemPalace Query", action: {
                        inputText = "Interoghează memoria episodică MemPalace pentru deciziile recente și rezumă contextul L0/L1."
                    })
                    QuickActionButton(title: "🛡️ Poartă Calitate AST", action: {
                        inputText = "Rulează poarta de calitate LoopGate pe fișierele modificate și raportează mutațiile AST."
                    })
                    QuickActionButton(title: "🔒 Scrub Secrete", action: {
                        inputText = "Scanează codebase-ul pentru credențiale neprotejate folosind entropia Shannon."
                    })
                    QuickActionButton(title: "🍎 App Store Audit", action: {
                        inputText = "Rulează auditul complet de App Store Compliance (Guideline 5.1.1 Privacy, 3.1.1 IAP, 2.1 Completeness) și raportează blocajele de lansare."
                    })
                    QuickActionButton(title: "🍎 Simulator iOS", action: {
                        inputText = "Listează simulatoarele iOS disponibile și pregătește un clean status bar la 9:41."
                    })
                    QuickActionButton(title: "🧹 Golește Chat", action: {
                        messages.removeAll()
                    })
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(NSColor.controlBackgroundColor).opacity(0.5))
                
                // Input Bar
                HStack(spacing: 10) {
                    TextField("Întreabă Harness-Suprem (\(client.engineStatus.modelName))...", text: $inputText)
                        .textFieldStyle(.roundedBorder)
                        .font(.system(size: 13))
                        .onSubmit {
                            sendMessage()
                        }
                    
                    if client.isGenerating {
                        Button(action: {
                            client.stopGeneration()
                        }) {
                            Image(systemName: "stop.circle.fill")
                                .font(.system(size: 20))
                                .foregroundColor(.red)
                        }
                        .buttonStyle(.plain)
                    } else {
                        Button(action: {
                            sendMessage()
                        }) {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.system(size: 22))
                                .foregroundColor(inputText.trimmingCharacters(in: .whitespaces).isEmpty ? .gray : .blue)
                        }
                        .buttonStyle(.plain)
                        .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color(NSColor.windowBackgroundColor))
            }
        }
        .frame(minWidth: 920, minHeight: 640)
        .onAppear {
            client.checkHealth()
        }
    }
    
    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        
        let userMsg = ChatMessage(role: "user", content: text)
        messages.append(userMsg)
        inputText = ""
        
        let assistantId = UUID()
        let placeholderMsg = ChatMessage(id: assistantId, role: "assistant", content: "", isStreaming: true)
        messages.append(placeholderMsg)
        
        // Build active plugins preamble
        let activePlugins = plugins.filter { $0.isEnabled }.map { $0.name }.joined(separator: ", ")
        var memorySection = ""
        if palace.isPalaceActive && !palace.status.wakeUpSnippet.isEmpty {
            memorySection = """
            
            [MEMPALACE EPISODIC CONTEXT (L0/L1)]:
            \(palace.status.wakeUpSnippet)
            """
        }
        
        let sysPrompt = """
        You are Harness-Suprem, the ultimate autonomous coding agent running locally on an Apple Silicon M1 Ultra with 128GB Unified Memory.
        Active Inference Engine: \(client.activeEngine.rawValue) on Port \(client.engineStatus.port).
        Active Model: \(client.engineStatus.modelName).
        Active Plugins (\(plugins.filter { $0.isEnabled }.count)/17): \(activePlugins).
        Safety & Quality: LoopGate AST checking: \(qualityGateEnabled), Secret Scrubber: \(securityScrubberEnabled), TDD: \(tddDisciplineEnabled).\(memorySection)
        Answer clearly, accurately, and assist with deep engineering and coding tasks.
        """
        
        client.streamCompletion(
            messages: messages.filter { $0.role != "system" && !$0.isStreaming },
            systemPrompt: sysPrompt,
            onToken: { token in
                if let idx = messages.firstIndex(where: { $0.id == assistantId }) {
                    messages[idx].content += token
                }
            },
            onComplete: { count, tps in
                if let idx = messages.firstIndex(where: { $0.id == assistantId }) {
                    messages[idx].isStreaming = false
                    messages[idx].tokensGenerated = count
                }
            }
        )
    }
}

// MARK: - Message Bubble Component
struct MessageBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.role == "user" {
                Spacer()
                Text(message.content)
                    .font(.system(size: 13))
                    .padding(12)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                    .textSelection(.enabled)
            } else {
                Image(systemName: "cpu.fill")
                    .foregroundColor(.orange)
                    .font(.system(size: 16))
                    .padding(.top, 4)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(LocalizedStringKey(message.content))
                        .font(.system(size: 13))
                        .padding(12)
                        .background(Color(NSColor.controlBackgroundColor))
                        .foregroundColor(.primary)
                        .cornerRadius(12)
                        .textSelection(.enabled)
                    
                    if message.tokensGenerated > 0 {
                        Text("\(message.tokensGenerated) tokens generated")
                            .font(.system(size: 9))
                            .foregroundColor(.secondary)
                            .padding(.leading, 4)
                    }
                }
                Spacer()
            }
        }
    }
}

// MARK: - Quick Action Button Component
struct QuickActionButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 11, weight: .medium))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
    }
}
