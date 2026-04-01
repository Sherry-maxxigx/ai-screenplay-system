# 使用Node.js官方镜像作为基础镜像
FROM node:16-alpine

# 设置工作目录
WORKDIR /app

# 复制package.json和package-lock.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm install

# 复制前端源代码
COPY frontend/ .

# 构建生产版本
RUN npm run build

# 使用Nginx作为Web服务器
FROM nginx:alpine

# 复制构建产物到Nginx静态目录
COPY --from=0 /app/dist /usr/share/nginx/html

# 复制Nginx配置文件
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]