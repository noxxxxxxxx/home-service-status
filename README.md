# 家庭服务状态页

GitHub Actions 每 15 分钟从外部网络检查 Penpot 和 SonarQube 的公开入口，并将状态发布到 GitHub Pages。页面检查后还会下载各服务主 JavaScript 文件的前 256 KiB，以识别首页可打开、资源却 502 或传输中断的情况。`public/history.json` 仅保留最近 7 天的采样。

## 部署

1. 在 GitHub 创建公开仓库，例如 `home-service-status`，推送本目录到 `main`。
2. 在仓库 **Settings → Pages → Build and deployment** 中选择 **GitHub Actions**。
3. 在 **Actions** 里手动运行 **Check and publish service status**，确认两个作业成功，再访问 Pages 地址。

状态页只包含公开域名与可访问性，不包含家庭 IP、服务器凭据或内部拓扑。GitHub Actions 的定时任务可能延迟或漏跑；页面在 45 分钟没有新检查时显示“监测延迟”。
