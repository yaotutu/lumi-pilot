# 其他语言客户端调用示例

## 项目结构

```
lumi-pilot/
├── protos/lumi_pilot.proto     # gRPC接口定义
├── generated/                  # Python生成代码
├── examples/                   # 客户端示例
└── main.py                    # 服务器启动入口
```

## 1. Node.js 客户端

### 安装依赖
```bash
npm install @grpc/grpc-js @grpc/proto-loader
```

### 生成代码 (可选)
```bash
# 复制proto文件到你的Node.js项目
cp protos/lumi_pilot.proto /path/to/your/nodejs/project/

# 或者直接使用proto-loader动态加载
```

### 客户端代码
```javascript
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

// 加载proto文件
const packageDefinition = protoLoader.loadSync('lumi_pilot.proto', {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});

const lumiPilot = grpc.loadPackageDefinition(packageDefinition).lumi_pilot;

// 创建客户端
const client = new lumiPilot.LumiPilotService('localhost:50051', grpc.credentials.createInsecure());

// 调用AI对话
const request = {
  message: "你好，我是Node.js客户端"
};

client.Chat(request, (error, response) => {
  if (error) {
    console.error('错误:', error);
    return;
  }
  
  if (response.success) {
    console.log('AI回复:', response.message);
    console.log('模型:', response.metadata.model);
    console.log('耗时:', response.metadata.duration + '秒');
  } else {
    console.error('服务错误:', response.error);
  }
});
```

## 2. Go 客户端

### 安装依赖
```bash
go mod init lumi-pilot-client
go get google.golang.org/grpc
go get google.golang.org/protobuf/cmd/protoc-gen-go
go get google.golang.org/grpc/cmd/protoc-gen-go-grpc
```

### 生成代码
```bash
# 创建输出目录
mkdir -p proto

# 生成Go代码
protoc --go_out=proto --go_opt=paths=source_relative \
       --go-grpc_out=proto --go-grpc_opt=paths=source_relative \
       --proto_path=. lumi_pilot.proto
```

### 客户端代码
```go
package main

import (
    "context"
    "log"
    "time"
    
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "path/to/your/proto"
)

func main() {
    // 连接到服务器
    conn, err := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        log.Fatalf("连接失败: %v", err)
    }
    defer conn.Close()
    
    // 创建客户端
    client := pb.NewLumiPilotServiceClient(conn)
    
    // 调用AI对话
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    request := &pb.ChatRequest{
        Message: "你好，我是Go客户端",
    }
    
    response, err := client.Chat(ctx, request)
    if err != nil {
        log.Fatalf("调用失败: %v", err)
    }
    
    if response.Success {
        log.Printf("AI回复: %s", response.Message)
        log.Printf("模型: %s", response.Metadata.Model)
        log.Printf("耗时: %.2f秒", response.Metadata.Duration)
    } else {
        log.Printf("服务错误: %s", response.Error)
    }
}
```

## 3. Java 客户端

### 添加依赖 (Maven)
```xml
<dependencies>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-netty-shaded</artifactId>
        <version>1.53.0</version>
    </dependency>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-protobuf</artifactId>
        <version>1.53.0</version>
    </dependency>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-stub</artifactId>
        <version>1.53.0</version>
    </dependency>
</dependencies>

<build>
    <extensions>
        <extension>
            <groupId>kr.motd.maven</groupId>
            <artifactId>os-maven-plugin</artifactId>
            <version>1.6.2</version>
        </extension>
    </extensions>
    <plugins>
        <plugin>
            <groupId>org.xolstice.maven.plugins</groupId>
            <artifactId>protobuf-maven-plugin</artifactId>
            <version>0.6.1</version>
            <configuration>
                <protocArtifact>com.google.protobuf:protoc:3.21.7:exe:${os.detected.classifier}</protocArtifact>
                <pluginId>grpc-java</pluginId>
                <pluginArtifact>io.grpc:protoc-gen-grpc-java:1.53.0:exe:${os.detected.classifier}</pluginArtifact>
            </configuration>
            <executions>
                <execution>
                    <goals>
                        <goal>compile</goal>
                        <goal>compile-custom</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

### 客户端代码
```java
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;

public class LumiPilotClient {
    public static void main(String[] args) {
        // 创建通道
        ManagedChannel channel = ManagedChannelBuilder.forAddress("localhost", 50051)
                .usePlaintext()
                .build();
        
        try {
            // 创建客户端
            LumiPilotServiceGrpc.LumiPilotServiceBlockingStub client = 
                LumiPilotServiceGrpc.newBlockingStub(channel);
            
            // 构建请求
            ChatRequest request = ChatRequest.newBuilder()
                    .setMessage("你好，我是Java客户端")
                    .build();
            
            // 调用服务
            ChatResponse response = client.chat(request);
            
            if (response.getSuccess()) {
                System.out.println("AI回复: " + response.getMessage());
                System.out.println("模型: " + response.getMetadata().getModel());
                System.out.println("耗时: " + response.getMetadata().getDuration() + "秒");
            } else {
                System.err.println("服务错误: " + response.getError());
            }
            
        } catch (StatusRuntimeException e) {
            System.err.println("调用失败: " + e.getStatus());
        } finally {
            channel.shutdown();
        }
    }
}
```

## 4. C# 客户端

### 安装包
```bash
dotnet add package Grpc.Net.Client
dotnet add package Google.Protobuf
dotnet add package Grpc.Tools
```

### 生成代码 (在.csproj中添加)
```xml
<ItemGroup>
  <Protobuf Include="lumi_pilot.proto" GrpcServices="Client" />
</ItemGroup>
```

### 客户端代码
```csharp
using Grpc.Net.Client;
using LumiPilot;

class Program
{
    static async Task Main(string[] args)
    {
        // 创建通道
        using var channel = GrpcChannel.ForAddress("http://localhost:50051");
        var client = new LumiPilotService.LumiPilotServiceClient(channel);
        
        // 构建请求
        var request = new ChatRequest
        {
            Message = "你好，我是C#客户端"
        };
        
        try
        {
            // 调用服务
            var response = await client.ChatAsync(request);
            
            if (response.Success)
            {
                Console.WriteLine($"AI回复: {response.Message}");
                Console.WriteLine($"模型: {response.Metadata.Model}");
                Console.WriteLine($"耗时: {response.Metadata.Duration}秒");
            }
            else
            {
                Console.WriteLine($"服务错误: {response.Error}");
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"调用失败: {e.Message}");
        }
    }
}
```

## 5. cURL 测试 (通过grpcurl)

### 安装grpcurl
```bash
# macOS
brew install grpcurl

# Linux
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
```

### 测试调用
```bash
# 列出服务
grpcurl -plaintext localhost:50051 list

# 查看服务方法
grpcurl -plaintext localhost:50051 list lumi_pilot.LumiPilotService

# 调用AI对话
grpcurl -plaintext -d '{
  "message": "你好，我是grpcurl客户端"
}' localhost:50051 lumi_pilot.LumiPilotService/Chat
```

## 接口说明

### 服务定义
- **服务名**: `lumi_pilot.LumiPilotService`
- **方法**: `Chat(ChatRequest) returns (ChatResponse)`
- **地址**: `localhost:50051`

### 请求参数
- `message`: 用户消息 (必需)

### 响应字段
- `success`: 是否成功
- `message`: AI回复内容
- `error`: 错误信息
- `metadata`: 响应元数据 (请求ID、模型、耗时等)