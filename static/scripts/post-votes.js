document.addEventListener('DOMContentLoaded', function () {
  var upvoteButtonsALL=document.querySelectorAll('.upvote');
  for(let i=0;i<upvoteButtonsALL.length;i++){
   document.querySelectorAll('.upvote')[i].addEventListener('click',postVote);
   }
      console.log(upvoteButtonsALL)

   var downVoteButtonsALL=document.querySelectorAll('.downvote');
   console.log(downVoteButtonsALL);
   for(let i=0;i<downVoteButtonsALL.length;i++){
   console.log('hello world')
   document.querySelectorAll('.downvote')[i].addEventListener('click',postVote);
   }
   var upvotecommentButtonsALL=document.querySelectorAll('.upvotecomment');
  for(let i=0;i<upvotecommentButtonsALL.length;i++){
   document.querySelectorAll('.upvotecomment')[i].addEventListener('click',commentVote);
   }
      console.log(upvotecommentButtonsALL)

   var downVotecommentButtonsALL=document.querySelectorAll('.downvotecomment');
   for(let i=0;i<downVotecommentButtonsALL.length;i++){
   console.log('hello world')
   document.querySelectorAll('.downvotecomment')[i].addEventListener('click',commentVote);
   }
}
);

function commentVote() {
  button=this
  var voteValue = button.getAttribute("data-vote");
  var commentID = button.getAttribute("data-comment");
  fetch('/commentVote', {
    headers: new Headers({
      "content-type": "application/json"
    }),
    method: 'POST',
    body: JSON.stringify({
        "voteValue": voteValue,
        "commentID": commentID
    })
  })

  .then(function (response) { // At this point, Flask has printed our JSON
    response.json().then(function(data) {
      if (response.status === 401) {
        location.reload();
      }

      else {
      console.log(data)
        if (data['toggleUpvote']==true) {
          document.querySelector('#comment-votes-' + data['commentID'] + ' [data-vote="1"] i.fa-arrow-up').classList.toggle('active');
        }

        if (data['toggleDownvote']) {
          document.querySelector('#comment-votes-' + data['commentID'] + ' [data-vote="-1"] i.fa-arrow-down').classList.toggle('active');
        }
        document.querySelector('#commentTotalVotes'+data['commentID']).innerText = data['updatedCommentTotal'];
      }
    });
  }).catch(function (error) {
      console.log("Fetch error: " + error['message']);
  });
}


function postVote() {
  button=this
  var voteValue = button.getAttribute("data-vote");
  var postID = button.getAttribute("data-post");
  fetch('/postVote', {
    headers: new Headers({
      "content-type": "application/json"
    }),
    method: 'POST',
    body: JSON.stringify({
        "voteValue": voteValue,
        "postID": postID
    })
  })

  .then(function (response) { // At this point, Flask has printed our JSON
    response.json().then(function(data) {
      if (response.status === 401) {
        location.reload();
      }

      else {
      console.log(data)
        if (data['toggleUpvote']==true) {
          document.querySelector('#post-votes-' + data['postID'] + ' [data-vote="1"] i.fa-arrow-up').classList.toggle('active');
        }

        if (data['toggleDownvote']) {
          document.querySelector('#post-votes-' + data['postID'] + ' [data-vote="-1"] i.fa-arrow-down').classList.toggle('active');
        }
        document.querySelector('#postTotalVotes'+data['postID']).innerText = data['updatedVoteTotal'];
      }
    });
  }).catch(function (error) {
      console.log("Fetch error: " + error['message']);
  });
}
