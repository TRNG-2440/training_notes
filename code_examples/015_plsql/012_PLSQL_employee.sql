/*
 * Commonly when creating functional entities (functions, views, sequences, etc...)
 * the CREATE, OR and REPLACE keywords are used together:
 * CREATE OR REPLACE <entity> ...
 */
CREATE OR REPLACE FUNCTION examples.count_emp_salary_range(
	min_sal INTEGER, max_sal INTEGER)
	RETURNS INTEGER AS 
	$$
	DECLARE 
		sal_count INTEGER;
	BEGIN 
		SELECT COUNT(*) INTO sal_count FROM examples.EMPLOYEES
		WHERE emp_salary BETWEEN min_sal AND max_sal;
		RETURN sal_count;		
	END
	$$ LANGUAGE PLPGSQL;
	
-- Use the select statement to call a function
SELECT count_emp_salary_range(90000, 160000);

/*
 * Creating Sequences allow for more control over the automatic
 * scaling of a value - can be used with ID (effectively our own
 * custom 'SERIAL')
 * 
 * Syntax:
 * 
 * CREATE SEQUENCE <sequence_name> 
 * 	START WITH <value> INCREMENT | DECREMENT BY <amount>
 */
CREATE SEQUENCE IF NOT EXISTS examples.emp_id_seq START WITH 2000 INCREMENT BY 1;

CREATE OR REPLACE FUNCTION examples.emp_id_func()
	RETURNS TRIGGER AS
$$ BEGIN
	IF NEW.emp_id IS NULL THEN
		NEW.emp_id:=NEXTVAL('examples.emp_id_seq');
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE PLPGSQL;

/*
 * Triggers : An entity that can perform some operation (typically invoking
 * a stored procedure or function) in response to another operation which
 * is called.  
 */
CREATE TRIGGER emp_id_trig
BEFORE INSERT ON examples.employees
FOR EACH ROW 
EXECUTE FUNCTION examples.emp_id_func();

DROP TRIGGER IF EXISTS emp_id_trig ON examples.employees;

-- This insert statement triggers the emp_id_trig, 
-- which in turn calls the emp_id_func()
INSERT INTO examples.employees (emp_name, emp_title, emp_salary) VALUES ('Rob', 'Developer', 97000);

-- USING SEQUENCES WITH DDL:
CREATE SEQUENCE IF NOT EXISTS login_id_seq START WITH 10000 INCREMENT BY 1;

/* You may reference a created sequence by name using the 'DEFAULT'
 * keyword within a DDL table creation statement
 */
CREATE TABLE user_login (
	login_id INTEGER DEFAULT nextval('login_id_seq') PRIMARY KEY,
	login_name VARCHAR(200),
	login_pass VARCHAR(200)
);

/*
 * Stored Procedure : An entity, similar to a function, which performs
 * operations, but does not return data
 */
CREATE OR REPLACE PROCEDURE examples.emp_percent_raise(
	percent_inc DEC, id INT
) LANGUAGE PLPGSQL
AS $$
BEGIN 
	UPDATE examples.EMPLOYEES 
	SET emp_salary = emp_salary * percent_inc
	WHERE emp_id = id;
COMMIT;
END $$

-- Invoke a stored procedure using the keyword 'Call'
CALL EMP_PERCENT_RAISE (1.1, 1000);
