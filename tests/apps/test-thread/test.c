#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <errno.h>

#define DEFPORT 6666
#define HEADMSG "Message:"
#define HEADLEN 8
#define MAXMSGLEN 1048576

struct Pipe {
    int fd_send;
    int fd_recv;
};

void *handle_chat(void *data) {
    struct Pipe *pipe = (struct Pipe *)data;
    char *buffer = malloc(MAXMSGLEN + HEADLEN);
    strncpy(buffer, HEADMSG, HEADLEN);
    char *bufp = buffer + HEADLEN;              /* recv()新接收数据的存放位置 */
    char *newlinep;
    size_t msglen = 0;                          /* 当前消息的长度 */
    ssize_t recvlen;                            /* 每次recv()得到的数据长度 */
    while ((recvlen = recv(pipe->fd_send, bufp, MAXMSGLEN - msglen, 0)) > 0) {
        while ((newlinep = (char *)memchr(bufp, '\n', recvlen)) != NULL) {
            /* 已经收到一条完整的消息 */
            size_t unsentlen = newlinep - buffer + 1;   /* 还要发送的数据长度 */
            ssize_t sentlen;                     /* 每次send()实际发送的数据长度 */
            char *sendp = buffer;
            while (unsentlen > 0) {
                /* 还没有全部发送出去 */
                if ((sentlen = send(pipe->fd_recv, sendp, unsentlen, 0)) <= 0) {
                    if (errno == EINTR)
                        sentlen = 0;
                    else {
                        perror("send");
                        exit(EXIT_FAILURE);
                    }
                }
                unsentlen -= sentlen;
                sendp += sentlen;
            }
            /* 剩余部分属于下一条消息，移动至buffer开头 */
            newlinep += 1;
            size_t leftlen = recvlen = (bufp + recvlen) - newlinep; /* 剩余部分的长度 */
            bufp = buffer + HEADLEN;
            for (; leftlen > 0; leftlen--, bufp++, newlinep++) *bufp = *newlinep;
            bufp = buffer + HEADLEN;
            msglen = 0;
        }
        bufp += recvlen;
        msglen += recvlen;
    }
    return NULL;
}

int main(int argc, char **argv) {
    int port;
    if (argc == 1) port = DEFPORT;
    else port = atoi(argv[1]);
    int fd;
    if ((fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket");
        return 1;
    }
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);
    socklen_t addr_len = sizeof(addr);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr))) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    if (listen(fd, 2)) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    int fd1 = accept(fd, NULL, NULL);
    int fd2 = accept(fd, NULL, NULL);
    if (fd1 == -1 || fd2 == -1) {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    pthread_t thread1, thread2;
    struct Pipe pipe1;
    struct Pipe pipe2;
    pipe1.fd_send = fd1;
    pipe1.fd_recv = fd2;
    pipe2.fd_send = fd2;
    pipe2.fd_recv = fd1;
    pthread_create(&thread1, NULL, handle_chat, (void *)&pipe1);
    pthread_create(&thread2, NULL, handle_chat, (void *)&pipe2);
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    return 0;
}

