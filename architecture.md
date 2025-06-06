# Hyper Core Architecture

This document describes the high-level architecture of the Hyper Core framework, including the responsibilities of each system and how they interact with each other.

## Overview

Hyper Core is a modular, plugin-based CLI framework that provides terminal applications with ncurses UI support. The architecture follows separation of concerns with clear interfaces between components.

```mermaid
graph TB
    subgraph "Application Layer"
        CLI[CLI Entry Point]
        App[Application Instance]
    end
    
    subgraph "Plugin System"
        PR[Plugin Registry]
        PL[Plugin Loader]
        PD[Plugin Discovery]
        Plugins[Plugin Instances]
    end
    
    subgraph "Command Framework"
        CR[Command Registry]
        BC[Base Command]
        Commands[Command Instances]
    end
    
    subgraph "UI Framework"
        NCF[NCurses Framework]
        RE[Render Engine]
        Components[UI Components]
        Themes[Theme System]
    end
    
    subgraph "Container System"
        DI[Simple Container]
        Services[Registered Services]
    end
    
    subgraph "Core Protocols"
        ICommand[ICommand]
        IPlugin[IPlugin]
        IWidget[IWidget]
        IService[IService]
    end
    
    CLI --> App
    App --> PR
    App --> CR
    App --> NCF
    App --> DI
    
    PR --> PL
    PR --> PD
    PL --> Plugins
    
    CR --> Commands
    Commands --> BC
    BC --> ICommand
    
    NCF --> RE
    NCF --> Components
    NCF --> Themes
    Components --> IWidget
    
    Plugins --> Commands
    Plugins --> Components
    Plugins --> Services
    Plugins --> IPlugin
    
    DI --> Services
    Services --> IService
    
    Commands --> DI
    Components --> DI
```

## System Components

### 1. Plugin System

The plugin system is responsible for discovering, loading, and managing plugins that extend the framework's functionality.

```mermaid
graph LR
    subgraph "Plugin System"
        PD[Plugin Discovery] --> PL[Plugin Loader]
        PL --> PR[Plugin Registry]
        PR --> PI[Plugin Instance]
    end
    
    subgraph "Plugin Structure"
        PP[Plugin Package]
        PM[plugin.py]
        PMF[plugin.yaml/json]
    end
    
    subgraph "Plugin Components"
        CMD[Commands]
        WID[Widgets]
        SVC[Services]
        PAG[Pages]
    end
    
    PD --> PP
    PP --> PM
    PP --> PMF
    PI --> CMD
    PI --> WID
    PI --> SVC
    PI --> PAG
```

**Responsibilities:**
- **Plugin Discovery**: Scans filesystem for valid plugin packages
- **Plugin Loader**: Loads Python modules and extracts metadata
- **Plugin Registry**: Manages loaded plugins and their components
- **Plugin Instance**: Provides runtime access to plugin functionality

**Key Files:**
- `src/hyper_core/plugins/loader.py` - Core loading logic
- `src/hyper_core/plugins/registry.py` - Plugin management

### 2. Command Framework

The command framework provides the structure for CLI commands with dependency injection and error handling.

```mermaid
graph TB
    subgraph "Command Framework"
        CR[Command Registry]
        BC[Base Command]
        IC[ICommand Protocol]
    end
    
    subgraph "Command Lifecycle"
        Init[Initialize with Container]
        Run[run() - Error Handling]
        Exec[execute() - Core Logic]
        Exit[Return Exit Code]
    end
    
    subgraph "Command Features"
        Progress[Progress Indicators]
        Console[Rich Console Output]
        Validation[Input Validation]
        Helpers[Path/Port Helpers]
    end
    
    CR --> BC
    BC --> IC
    BC --> Init
    Init --> Run
    Run --> Exec
    Exec --> Exit
    BC --> Progress
    BC --> Console
    BC --> Validation
    BC --> Helpers
```

**Responsibilities:**
- **Command Registry**: Manages available commands
- **Base Command**: Provides common functionality and utilities
- **Error Handling**: Standardized exception handling and exit codes
- **Console Output**: Rich formatting and progress indicators

**Key Files:**
- `src/hyper_core/commands/base.py` - Base command implementation
- `src/hyper_core/commands/registry.py` - Command management

### 3. UI Framework

The UI framework provides ncurses-based terminal interfaces with modern rendering architecture.

```mermaid
graph TB
    subgraph "UI Framework"
        NCF[NCurses Framework]
        RE[Render Engine]
        RB[Render Backend]
    end
    
    subgraph "UI Components"
        AF[Application Frame]
        CP[Content Panel]
        BW[Base Widget]
        UIC[UI Components]
    end
    
    subgraph "Rendering Pipeline"
        DC[Dirty Checking]
        DB[Double Buffering]
        OPT[Optimization]
        Draw[Screen Drawing]
    end
    
    subgraph "Theme System"
        TM[Theme Manager]
        TC[Theme Colors]
        IT[IThemeable]
    end
    
    NCF --> RE
    RE --> RB
    RE --> DC
    DC --> DB
    DB --> OPT
    OPT --> Draw
    
    NCF --> AF
    AF --> CP
    CP --> BW
    BW --> UIC
    
    TM --> TC
    UIC --> IT
    TM --> UIC
```

**Responsibilities:**
- **NCurses Framework**: Main UI orchestration and event handling
- **Render Engine**: Optimized rendering with dirty checking
- **Components**: Reusable UI building blocks
- **Theme System**: Consistent visual styling

**Key Files:**
- `src/hyper_core/ui/framework.py` - Main framework
- `src/hyper_core/ui/engine.py` - Rendering engine
- `src/hyper_core/ui/components.py` - UI components

### 4. Container System

The container system provides dependency injection for plugins and components.

```mermaid
graph LR
    subgraph "Container System"
        SC[Simple Container]
        BC[Base Container]
        CF[Container Factory]
    end
    
    subgraph "Service Management"
        SI[Service Instances]
        SF[Service Factories]
        SL[Service Lifecycle]
    end
    
    subgraph "DI Features"
        REG[Registration]
        RES[Resolution]
        SING[Singleton Management]
        OPT[Optional Dependencies]
    end
    
    SC --> BC
    CF --> SC
    SC --> SI
    SC --> SF
    SC --> SL
    
    SC --> REG
    SC --> RES
    SC --> SING
    SC --> OPT
```

**Responsibilities:**
- **Simple Container**: Lightweight DI for basic needs
- **Service Registration**: Register instances and factories
- **Service Resolution**: Retrieve services with dependency resolution
- **Lifecycle Management**: Singleton patterns and cleanup

**Key Files:**
- `src/hyper_core/container/simple_container.py` - Main container implementation
- `src/hyper_core/container/base_container.py` - Advanced container features

## Data Flow

### Plugin Loading Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant PR as Plugin Registry
    participant PD as Plugin Discovery
    participant PL as Plugin Loader
    participant PI as Plugin Instance
    
    App->>PR: initialize(plugin_paths)
    PR->>PD: discover_plugins()
    PD->>PD: scan filesystem
    PD-->>PR: plugin_paths[]
    
    loop For each plugin
        PR->>PL: load_plugin(path)
        PL->>PL: load_module()
        PL->>PL: extract_metadata()
        PL-->>PR: plugin_info
        PR->>PI: create instance
        PI->>PI: register components
        PI-->>PR: component_registry
    end
    
    PR-->>App: loaded_plugins[]
```

### Command Execution Flow

```mermaid
sequenceDiagram
    participant User as User Input
    participant App as Application
    participant CR as Command Registry
    participant CMD as Command Instance
    participant DI as Container
    
    User->>App: command_name + args
    App->>CR: get_command(name)
    CR-->>App: command_class
    App->>DI: get dependencies
    DI-->>App: services
    App->>CMD: create instance(container)
    CMD->>CMD: run(args)
    CMD->>CMD: execute(args)
    CMD-->>App: exit_code
    App-->>User: result/output
```

### UI Rendering Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant NCF as NCurses Framework
    participant RE as Render Engine
    participant Comp as UI Components
    participant Screen as Terminal
    
    App->>NCF: run()
    NCF->>RE: initialize()
    
    loop Main Loop
        NCF->>RE: render_frame()
        RE->>RE: check_dirty_components()
        alt Components dirty
            RE->>Comp: render(context)
            Comp->>Comp: draw_content()
            Comp-->>RE: rendered_content
            RE->>Screen: update_regions()
        end
        
        NCF->>NCF: handle_input()
        NCF->>Comp: process_events()
        Comp->>Comp: update_state()
        Comp->>RE: mark_dirty()
    end
```

## Plugin Integration Points

Plugins integrate with the framework through several well-defined interfaces:

1. **Command Integration**: Plugins provide command classes implementing `ICommand`
2. **Widget Integration**: Plugins provide widget classes implementing `IWidget`
3. **Service Integration**: Plugins provide service classes implementing `IService`
4. **Theme Integration**: Components implement `IThemeable` for styling

## Extension Points

The framework provides multiple extension points for customization:

- **Plugin Discovery**: Custom discovery mechanisms
- **Container Configuration**: Advanced DI setup
- **Theme Development**: Custom visual themes
- **Rendering Backends**: Alternative rendering systems
- **Command Parsers**: Custom argument parsing

## Performance Considerations

- **Lazy Loading**: Plugins and services loaded on-demand
- **Dirty Checking**: UI components only re-render when changed
- **Double Buffering**: Smooth terminal updates
- **Singleton Management**: Efficient service instantiation
- **Event-Driven Updates**: Minimal processing overhead