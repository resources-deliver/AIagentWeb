# AI Agent 语音功能实现方案

## 📋 功能概述

本项目已实现完整的语音输入和语音回答功能，使用 **Microsoft Edge-TTS** 作为语音合成引擎，支持 **16 种语言和方言**。

---

## 🎤 语音输入功能

### 实现方案

**技术栈：**
- **Web Speech API** (SpeechRecognition)
- 浏览器原生支持（Chrome、Edge 等）

**核心代码位置：**
- 前端：`public/app.js` - `setupRecognition()` 函数

**功能特点：**
1. ✅ 实时语音转文字
2. ✅ 支持多语言识别（根据选择的语言自动切换）
3. ✅ 语音输入完成后自动发送
4. ✅ 数字人头像显示"正在听你说话"状态

**使用方式：**
1. 点击"语音输入"按钮
2. 对着麦克风说话
3. 系统自动识别并转换为文字
4. 识别完成后自动发送消息

**支持的语言：**
- 普通话、粤语、台湾国语
- 美式英语、英式英语、澳式英语
- 日语、韩语
- 法语、德语、西班牙语
- 葡萄牙语、意大利语、俄语

---

## 🔊 语音回答功能

### 实现方案

**技术栈：**
- **Microsoft Edge-TTS** (edge-tts Python 库)
- **HTML5 Audio API** (前端播放)

**核心代码位置：**
- 后端：`app.py` - `/api/tts` 接口、`synthesize_speech()` 函数
- 前端：`public/app.js` - `speak()` 函数

**功能特点：**
1. ✅ 自动播放 AI 回答（默认开启）
2. ✅ 支持 16 种语言的语音合成
3. ✅ 多语言发音人选择（每个语言有专属 Neural 语音）
4. ✅ 语音参数可调节（语速、音量、音调）
5. ✅ 播放状态实时反馈（头像动画、状态提示）

**语音合成流程：**
```
用户发送消息 → AI 生成回答 → 文本净化 → Edge-TTS 合成 → 返回音频流 → 前端播放
```

**支持的语音（部分示例）：**
| 语言 | 语音人 | 特点 |
|------|--------|------|
| 普通话 | zh-CN-XiaoxiaoNeural | 温柔女声 |
| 粤语 | zh-HK-HiuGaaiNeural | 自然粤语 |
| 台湾国语 | zh-TW-HsiaoYuNeural | 台湾腔国语 |
| 美式英语 | en-US-JennyNeural | 标准美音 |
| 英式英语 | en-GB-SoniaNeural | 优雅英音 |
| 日语 | ja-JP-NanamiNeural | 自然日语女声 |
| 韩语 | ko-KR-SunHiNeural | 清晰韩语 |

---

## 🎬 口型和动画特效

### 实现方案

**技术栈：**
- **CSS3 Animations**
- **JavaScript 状态管理**

**核心代码位置：**
- 样式：`public/styles.css` - 动画关键帧
- 逻辑：`public/app.js` - `setAvatar()` 函数

### 动画效果

#### 1. **说话时的口型动画** 🗣️
- **语音条跳动**：3 个语音条不同频率跳动
- **头像轻微晃动**：模拟说话时的头部运动
- **光晕效果**：头像周围光晕脉动

**CSS 类：** `.is-speaking`

**动画关键帧：**
```css
@keyframes voiceBarEnhanced {
  0% { height: 6px; opacity: 0.6; }
  50% { height: 24px; opacity: 1; }
  100% { height: 18px; opacity: 0.9; }
}

@keyframes avatarTalk {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

@keyframes avatarGlow {
  0%, 100% { opacity: 0.8; transform: scale(1.08); }
  50% { opacity: 1; transform: scale(1.12); }
}
```

#### 2. **思考时的动画** 💭
- **脉冲光晕**：橙色光晕脉动（类似"正在思考"的视觉效果）
- **浮动效果**：头像轻微上下浮动和旋转
- **状态指示点**：变为橙色

**CSS 类：** `.is-thinking`

**动画关键帧：**
```css
@keyframes thinkingPulse {
  0%, 100% { 
    opacity: 0.6; 
    box-shadow: 0 0 20px rgba(255, 180, 97, 0.4);
  }
  50% { 
    opacity: 1; 
    box-shadow: 0 0 40px rgba(255, 180, 97, 0.8);
  }
}

@keyframes thinkingFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-5px) rotate(1deg); }
}
```

#### 3. **待机状态** 😊
- **绿色状态点**：表示系统就绪
- **静态头像**：无动画效果

---

## 🎛️ 用户控制

### 语音开关
- **按钮**：点击"语音已开/语音已关"切换
- **默认状态**：开启
- **关闭时**：停止当前播放，头像回到待机状态

### 语言选择
- **下拉菜单**：选择 16 种语言之一
- **自动切换**：
  - 语音识别语言
  - TTS 语音合成声音
  - AI 回答语言风格

---

## ⚙️ 技术配置

### 后端配置（app.py）

```python
# Edge-TTS 参数（可通过 .env 文件配置）
EDGE_TTS_RATE = "+0%"      # 语速：-100% 到 +100%
EDGE_TTS_VOLUME = "+0%"    # 音量：-100% 到 +100%
EDGE_TTS_PITCH = "+0Hz"    # 音调：-50Hz 到 +50Hz

# 自定义语音（.env 文件）
EDGE_VOICE_ZH_CN = "zh-CN-XiaoxiaoNeural"
EDGE_VOICE_EN_US = "en-US-JennyNeural"
# ... 其他语言
```

### 前端配置（app.js）

```javascript
// 状态管理
const state = { 
    ttsEnabled: true,          // 默认开启语音
    isSpeaking: false,         // 是否正在说话
    currentAudio: null,        // 当前音频对象
    currentVoiceLabel: ""      // 当前语音名称
};

// 语言元数据
const languageMeta = {
    "zh-CN": { label: "普通话", lang: "zh-CN" },
    "zh-HK": { label: "粤语", lang: "zh-HK" },
    // ... 其他语言
};
```

---

## 🚀 使用流程

### 1. **语音输入 → 文字发送**
```
点击"语音输入" → 说话 → 自动识别 → 显示文字 → 自动发送
```

### 2. **AI 回答 → 语音播放**
```
接收消息 → AI 思考（头像思考动画） → 生成回答 → 
合成语音（头像思考动画） → 播放语音（头像说话动画） → 播放完成
```

### 3. **状态变化**
```
待机中 → 听你说话（语音输入） → 思考中（AI 处理） → 
合成语音（TTS） → 播报中（播放音频） → 待机中
```

---

## 🎯 特色功能

### 1. **自动语音播放**
- AI 回答后自动播放语音
- 无需手动点击播放按钮

### 2. **多语言智能切换**
- 切换语言后，自动更新：
  - 语音识别引擎
  - TTS 合成声音
  - AI 回答风格

### 3. **文本净化**
- 自动过滤代码块、链接、emoji、特殊符号
- 确保 TTS 播放流畅自然

### 4. **错误处理**
- 浏览器不支持语音输入 → 显示提示
- TTS 服务不可用 → 降级为文字回答
- 播放失败 → 显示错误信息

### 5. **视觉反馈**
- 实时状态更新（状态栏文字）
- 丰富的动画效果（说话、思考、待机）
- 语音条跳动（模拟口型）

---

## 📊 性能优化

1. **音频流式传输**：Edge-TTS 使用流式合成，减少等待时间
2. **状态缓存**：TTS 可用性检测带 5 分钟缓存
3. **内存管理**：自动清理旧音频对象和 URL
4. **消息限制**：最多存储 24 条消息，防止内存泄漏

---

## 🔮 未来扩展

### 可选的 TTS 方案
1. **Azure Cognitive Services TTS** - 更高质量的 Neural 语音
2. **Google Cloud TTS** - 支持更多语言
3. **Amazon Polly** - AWS 集成
4. **本地 TTS** - 如 VITS、Tacotron2（离线使用）

### 增强功能
1. **语音唤醒** - "Hey AI" 唤醒词
2. **声纹识别** - 多用户区分
3. **情感语音** - 根据内容调整语气
4. **实时打断** - 播放中可打断 AI

---

## 📝 总结

本项目已实现**完整的语音交互系统**：

✅ **语音输入**：Web Speech API，支持多语言识别  
✅ **语音回答**：Edge-TTS，16 种语言 Neural 语音  
✅ **口型动画**：CSS3 动画，说话/思考状态可视化  
✅ **多语言支持**：自动切换识别和合成语言  
✅ **用户控制**：语音开关、语言选择、状态反馈  

**无需额外配置，开箱即用！** 🎉
