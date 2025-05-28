let headers = new Headers();
headers.append('Content-Type', 'application/json');
headers.append('Accept', 'application/json');


function getAnswers(question) {
    fetch(`${window.location.href}get_answers`, {
        method: 'POST',
        body: JSON.stringify({
           'question':question
        }),
        headers: headers,
        mode: 'cors'
    })
    .then(response => response.json())
    .then(res => {
        console.log('res',res)
        window.vueApp.msgList = res
        window.vueApp.isGeneratingAnswer = false
        window.vueApp.question = ''
        // setTimeout(()=>{
        //     window.vueApp.question = ''
        // },200)
        window.vueApp.$nextTick(() => {
            // 获取 chat-container 的 DOM 元素
            const chatContainer = document.querySelector('.chat-container');
            // 设置滚动条位置为容器的底部
            chatContainer.scrollTop = chatContainer.scrollHeight -20 ;
        });
        
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        // window.vueApp.isGeneratingAnswer = false
        // window.vueApp.isCanvasLoading = false
        // window.vueApp.$message({
        //     type: 'error',
        //     message: `Unknown Backend Error`
        //   });
    });
}

function getHistory(){
    fetch(`${window.location.href}get_history`, {
        method: 'GET',
        headers: headers,
        mode: 'cors'
    })
    .then(response => response.json())
    .then(res => {
        console.log('res',res)
        window.vueApp.msgList = res
        // setTimeout(()=>{
        //     window.vueApp.question = ''
        // },200)
        
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
}



function deleleMsg(index) {
    fetch(`${window.location.href}del_msg`, {
        method: 'POST',
        body: JSON.stringify({
           'index':index
        }),
        headers: headers,
        mode: 'cors'
    })
    .then(response => response.json())
    .then(res => {
        console.log('res',res)
        window.vueApp.msgList = res
        window.vueApp.isGeneratingAnswer = false
   
    })
    .catch(error => {
        console.error('Error fetching data:', error);
        // window.vueApp.isGeneratingAnswer = false
        // window.vueApp.isCanvasLoading = false
        // window.vueApp.$message({
        //     type: 'error',
        //     message: `Unknown Backend Error`
        //   });
    });
}
