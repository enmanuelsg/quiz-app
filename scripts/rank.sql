SELECT 
	au.username,
	count(au.username) as total_quiz,
	sum(qa.is_correct) as correct_quiz,
	round(avg(qa.is_correct), 2) as score
FROM  quiz_answer qa
INNER JOIN quiz_quizattempt qq ON qa.quiz_attempt_id = qq.id
INNER JOIN auth_user au ON qq.user_id = au.id
GROUP by au.username;